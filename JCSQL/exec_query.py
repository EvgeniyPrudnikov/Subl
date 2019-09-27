import sublime
import sublime_plugin
import sys
import os
import JCSQL.lib as lib


SETTINGS_FILE_NAME = 'JCSQL.sublime-settings'


class ExecQueryCommand(sublime_plugin.WindowCommand):
    def run(self, schema_name="", is_full_res="0", qtype="oracle_query", **kwargs):
        settings = sublime.load_settings(SETTINGS_FILE_NAME)

        tool, tmp_file_name = lib.prepare_query_file(self.window.active_view(), qtype)

        if not tool:
            print('Some errors occurred')
            return

        self.window.run_command("exec_thread", {"schema_name":schema_name, "tool":tool, "qtype": qtype, "is_full_res":is_full_res, "tmp_file_name":tmp_file_name})