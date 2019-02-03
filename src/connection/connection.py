import time
import re
from threading import Lock, Thread

from src.utility.exceptions import OperationError
from src.utility.settings import Settings


class Connection:
    def __init__(self, terminal=None):
        self._terminal = terminal
        self._reader_running = False
        self._auto_read_enabled = True
        self._auto_reader_lock = Lock()

    def is_connected(self):
        raise NotImplementedError()

    def disconnect(self):
        raise NotImplementedError()

    def read_line(self):
        raise NotImplementedError()

    def read_all(self):
        raise NotImplementedError()

    def read_junk(self):
        self.read_all()

    def read_one_byte(self):
        raise NotImplementedError()

    def read_to_next_prompt(self, timeout=5.0):
        ret = b""
        t_start = time.time()
        while len(ret) < 4 or ret[-4:] != b">>> ":
            if (time.time() - t_start) >= timeout:
                raise TimeoutError()
            ret += self.read_one_byte()
        return ret.decode("utf-8", errors="replace")

    def send_line(self, line_text, ending="\r\n"):
        raise NotImplementedError()

    def send_character(self, char):
        raise NotImplementedError()

    def send_bytes(self, binary):
        raise NotImplementedError()

    def send_block(self, text):
        lines = text.split("\n")
        if len(lines) == 1:
            self.send_line(lines[0])
        elif len(lines) > 1:
            self.send_start_paste()
            for line in lines:
                self.send_line(line)
            self.send_end_paste()

    def run_file(self, file_name, globals_init=""):
        self.send_start_paste()
        if globals_init:
            self.send_line(globals_init, "\r")
        self.send_line("with open(\"{}\") as f:".format(file_name))
        self.send_line("    exec(f.read(), globals())")
        self.send_end_paste()

    def get_file_size(self, file_name):
        success = True
        file_size = 0
        self._auto_reader_lock.acquire()
        self._auto_read_enabled = False
        self.send_line("import os; os.stat(\"{}\")".format(file_name))
        try:
            res = self.read_to_next_prompt()
            # Skip first line which is command echo
            res = res[res.find("\n"):]
            # Strip parentheses and split to items
            items = res.strip("()\r\n ").split(", ")
            # Sixth item is file size
            file_size = int(items[6])
        except TimeoutError:
            success = False
        self._auto_read_enabled = True
        self._auto_reader_lock.release()
        if not success:
            raise OperationError()
        return file_size

    def send_start_paste(self):
        self.send_character("\5")

    def send_end_paste(self):
        self.send_character("\4")

    def send_kill(self):
        self.send_character("\3")

    def _reader_thread_routine(self):
        self._reader_running = True
        while self._reader_running:
            self._auto_reader_lock.acquire()
            x = ""
            if self._auto_read_enabled:
                x = self.read_line()
            self._auto_reader_lock.release()
            time.sleep(0.1 if not x else 0)

    @staticmethod
    def _get_remote_file_name(local_file_path,mcu_dir):
        return mcu_dir + local_file_path.rsplit("/", 1)[1]

    def list_files(self,mcu_folder="/"):
        success = True
        # Pause autoreader so we can receive response
        self._auto_reader_lock.acquire()
        self._auto_read_enabled = False
        # Stop any running script
        self.send_kill()
        # Read any leftovers
        self.read_junk()
        # Mark the start of file listing communication
        self.send_line("print('#fs#')")
        # Now we either wait for any running program to finish
        # or read output that it might be producing until it finally
        # closes and our command gets executed.
        ret = ""
        while "#fs#" not in ret:
            try:
                ret = self.read_to_next_prompt()
            except TimeoutError:
                success = False
        # Now we can be sure that we are ready for listing files
        # Send command for listing files
        # With os.listdir, the path must not end with "/" (unless it's the root, in which case "/" is equivalent to "")
        if success:
            line = "import os; [chr(35+(os.stat(\""+mcu_folder+"\"+fn)[0] == 32768))+fn for fn in os.listdir(\""+mcu_folder[:-1]+"\")]"
            self.send_line(line)
            # Wait for reply
            try:
                ret = self.read_to_next_prompt()
            except TimeoutError:
                success = False
        self._auto_read_enabled = True
        self._auto_reader_lock.release()

        if success and ret:
            return re.findall("'([^']+)'", ret)
        else:
            raise OperationError()

    def _make_dir_job(self, file_name, transfer):
        self._auto_reader_lock.acquire()
        self._auto_read_enabled = False
        if Settings().use_transfer_scripts:
            self.send_line("import os; os.mkdir(\"{}\")".format(file_name))
        else:
            raise NotImplementedError()

        transfer.mark_finished()
        self._auto_read_enabled = True
        self._auto_reader_lock.release()

    def make_dir(self, file_name, transfer):
        job_thread = Thread(target=self._make_dir_job,
                            args=(file_name, transfer))
        job_thread.setDaemon(True)
        job_thread.start()

    def _write_file_job(self, remote_name, content, transfer):
        raise NotImplementedError()

    def write_file(self, file_name, text, transfer):
        job_thread = Thread(target=self._write_file_job,
                            args=(file_name, text, transfer))
        job_thread.setDaemon(True)
        job_thread.start()

    def _write_files_job(self, local_file_paths, mcu_dir, transfer, set_text=None):
        n_files = len(local_file_paths)

        for i in range(n_files):
            local_path  = local_file_paths[i]
            remote_name = self._get_remote_file_name(local_path, mcu_dir)
            if set_text is not None:
                s = "Saving '%s' (%d/%d)." % (remote_name,i+1,n_files)
                set_text(s)

            with open(local_path, "rb") as f:
                content = f.read()
                self._write_file_job(remote_name, content, transfer)
                if transfer.cancel_scheduled:
                    transfer.confirm_cancel()
                if transfer.error or transfer.cancelled:
                    break

    def write_files(self, local_file_paths, mcu_dir, transfer, set_text=None):
        job_thread = Thread(target=self._write_files_job,
                            args=(local_file_paths, mcu_dir, transfer, set_text))
        job_thread.setDaemon(True)
        job_thread.start()

    def _write_steps_job(self, root_dir, path_steps, transfer, set_text=None):
        n_steps = len(path_steps)

        for i in range(n_steps):
            local_path,remote_name = path_steps[i]
            title = "Step %d/%d: " % (i+1,n_steps)

            if local_path is None:
                title += "Creating folder "+remote_name
                if set_text is not None: set_text(title)
                self._make_dir_job(remote_name, transfer)
            else:
                title += "Uploading ..."+local_path.replace(root_dir,"")
                if set_text is not None: set_text(title)
                with open(local_path, "rb") as f:
                    content = f.read()
                    self._write_file_job(remote_name, content, transfer)
                    if transfer.cancel_scheduled:
                        transfer.confirm_cancel()
                    if transfer.error or transfer.cancelled:
                        break

            if transfer.error or transfer.cancelled:
                break

    def write_steps(self, root_dir, path_steps, transfer, set_text=None):
        job_thread = Thread(target=self._write_steps_job,
                            args=(root_dir, path_steps, transfer, set_text))
        job_thread.setDaemon(True)
        job_thread.start()

    def _remove_file_job(self, file_name, transfer, set_text):
        #TODO use translate (?)
        s = "Removing %s, please wait..." % file_name
        if set_text is not None: set_text(s)
        self._auto_reader_lock.acquire()
        self._auto_read_enabled = False

        success = False
        if Settings().use_transfer_scripts:
            self.send_line("import __upl; __upl.remove(\"{}\")".format(file_name))
        else:
            #This will only remove files, not folders
            self.send_line("import os; os.remove(\"{}\")".format(file_name))
        try:
            self.read_to_next_prompt()
            success = True
        except TimeoutError:
            success = False

        transfer.mark_finished()
        self._auto_read_enabled = True
        self._auto_reader_lock.release()

        if not success:
            raise OperationError()

    def remove_file(self, file_name, transfer, set_text=None):
        job_thread = Thread(target=self._remove_file_job,
                            args=(file_name, transfer, set_text))
        job_thread.setDaemon(True)
        job_thread.start()

    def _read_file_job(self, file_name, transfer):
        raise NotImplementedError()

    def read_file(self, file_name, transfer):
        job_thread = Thread(target=self._read_file_job, args=(file_name, transfer))
        job_thread.setDaemon(True)
        job_thread.start()
