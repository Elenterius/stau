import ast
from os import walk


class ParsingError(Exception):
    def __init__(self, errors, message):
        super().__init__(message)
        self.errors = errors


class OdfParser:

    def __init__(self, root_path):
        self.root_path = root_path
        self.cached_folders = {}
        self.cached_odfs = {}

        for (dir_path, dir_names, file_names) in walk(root_path):
            if len(file_names) > 0:
                folder_path = dir_path.replace(root_path, '')
                self.cached_folders[folder_path] = file_names

    def get_folder_for_file(self, file_name):
        for cached_folder_name, cached_file_names in self.cached_folders.items():
            for cached_file_name in cached_file_names:
                if file_name.lower() == cached_file_name.lower():
                    return cached_folder_name
        return None

    def print_file(self, file_name):
        folder_name = self.get_folder_for_file(file_name)
        if folder_name:
            file_path = self.root_path + folder_name + '\\' + file_name
            with open(file_path, 'r') as f:
                for line in f:
                    print(line)

    def parse_all(self):
        for folder_name, file_names in self.cached_folders.items():
            for file_name in file_names:
                self.__parse_odf(file_name, folder_name)

        return self.cached_odfs

    def parse_odf(self, file_name, folder_name=None):
        if folder_name is None:
            folder_name = self.get_folder_for_file(file_name)

        if folder_name:
            self.__parse_odf(file_name, folder_name)
            return self.cached_odfs[file_name]

        return None

    def __process_include(self, line, curr_folder_name, file_name):
        include_odf = line.replace('#include', '').replace('"', '').strip()

        parsed = False
        for fname in self.cached_folders[curr_folder_name]:
            if include_odf.lower() == fname.lower():
                # use real filename (mitigates include filename mismatching real filename)
                include_odf = fname
                self.__parse_odf(include_odf, curr_folder_name)
                parsed = True
                break
        if not parsed:
            for folder_name, file_names in self.cached_folders.items():
                if folder_name != curr_folder_name:
                    for fname in file_names:
                        if include_odf.lower() == fname.lower():
                            include_odf = fname
                            self.__parse_odf(include_odf, folder_name)
                            break
        # copy content of included odf
        for k, v in self.cached_odfs[include_odf].items():
            self.cached_odfs[file_name][k] = v

    def __process_value(self, raw_value, file_name, curr_key):
        try:
            return ast.literal_eval(raw_value)
        except SyntaxError as se:
            raise ParsingError(
                se.args[0], 'in "{}" at "{}" --> {}'.format(file_name, curr_key, raw_value))
        except ValueError as ve:
            raise ParsingError(
                ve.args[0], 'in "{}" at "{}" --> {}'.format(file_name, curr_key, raw_value))

    def __process_node(self, raw_value, file_name, curr_key):
        try:
            values = raw_value.split()
            value = []
            for v in values:
                v = v.strip()
                if v != '':
                    value.append(self.__process_value(v, file_name, curr_key))
            if len(value) > 1:
                return value
            else:
                return value[0]
        except Exception:
            raise

    def __process_float(self, raw_value, file_name, curr_key):
        try:
            return self.__process_node(raw_value.replace('f', ''), file_name, curr_key)
        except Exception as e:
            print('[FloatParsingError]:', e.errors, e)
            return 0.0

    def __process_string(self, raw_value, file_name, curr_key):
        if raw_value.count('"') > 2:
            values = raw_value.split('"')
            value = []
            for v in values:
                v = v.strip()
                if v != '':
                    # ast.literal_eval(v) not needed
                    value.append(v)
            return value
        else:
            try:
                return self.__process_value(raw_value, file_name, curr_key)
            except Exception as e:
                print('[StringParsingError]:', e.errors, e)
                return ''

    def __parse_odf(self, file_name, curr_folder_name):
        if file_name in self.cached_odfs:
            return

        file_path = self.root_path + curr_folder_name + '\\' + file_name
        with open(file_path, 'r') as f:
            self.cached_odfs[file_name] = {}
            is_multiline_value = False
            curr_key = None
            curr_value = []

            for line in f:
                line = line.strip()

                if line.startswith('#include'):
                    self.__process_include(line, curr_folder_name, file_name)

                # skip comment or empty line
                elif line.startswith('//') or line.startswith('#') or line == '':
                    # if value_in_nextline:
                    #     value_in_nextline = False
                    #     self.cached_odfs[file_name][curr_key] = curr_value
                    #     curr_value = []
                    continue

                elif line != '':

                    # new attribute assignment
                    if '=' in line:

                        # finish previous multiline assignment
                        if is_multiline_value:
                            is_multiline_value = False
                            self.cached_odfs[file_name][curr_key] = curr_value
                            curr_value = []

                        keypair = line.split('=')
                        curr_key = keypair[0].strip()
                        if len(keypair) == 2:
                            value = keypair[1].strip()

                            # remove illegal character
                            value = value.replace(';', '')

                            # remove any trailing comment if present
                            if '//' in value:
                                value = value[:value.find('//')]
                            if '#' in value:
                                value = value[:value.find('#')]

                            if '"' in value:  # string value
                                self.cached_odfs[file_name][curr_key] = self.__process_string(
                                    value, file_name, curr_key)
                            elif 'f' in value:  # float value
                                self.cached_odfs[file_name][curr_key] = self.__process_float(
                                    value, file_name, curr_key)
                            elif value != '':
                                # not string or float value
                                try:
                                    self.cached_odfs[file_name][curr_key] = self.__process_node(
                                        value, file_name, curr_key)
                                except Exception as e:
                                    print('[UnknownValueParsingError]:', e.errors, e)
                                    self.cached_odfs[file_name][curr_key] = None

                            else:
                                is_multiline_value = True
                                curr_value = []
                                self.cached_odfs[file_name][curr_key] = None

                        else:
                            is_multiline_value = True
                            curr_value = []
                            self.cached_odfs[file_name][curr_key] = None

                    # //TODO: refactor this
                    elif is_multiline_value:
                        value = None
                        if 'f' in line:  # float value
                            value = line.replace('f', '')
                            value = ast.literal_eval(value)
                        elif '"' in line:  # string value
                            if line.count('"') > 2:  # is array
                                values = line.split('"')
                                value = []
                                for v in values:
                                    v = v.strip()
                                    if v != '':
                                        # ast.literal_eval(v) no longer needed
                                        value.append(v)
                            else:  # is one value
                                value = ast.literal_eval(line)
                        else:  # not string or float value
                            value = ast.literal_eval(line)

                        if type(value) is list:
                            curr_value.extend(value)
                        else:
                            curr_value.append(value)

            # reached end of file, store remaining values
            if is_multiline_value:
                is_multiline_value = False
                self.cached_odfs[file_name][curr_key] = curr_value
                curr_value = []
