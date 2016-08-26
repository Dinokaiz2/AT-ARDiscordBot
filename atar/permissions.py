class PermissionsDefaults:
    permsFile = 'config/permissions.ini'

    CommandWhiteList = set()
    CommandBlackList = set()
    GrantToRoles = set()
    UserList = set()

class Permissions:
    def __init__(self, configFile, grantAll=None):
        self.configFile = configFile
        self.config = configparser.ConfigParser(interpolation=None)

        if not self.config.read(configFile, encoding='utf-8'):
            print('[permissions] Permissions file not found, copying example_permissions.ini')

            try:
                shutil.copy('config/example_permissions.ini', configFile)
                self.config.read(configFile, encoding='utf-8')

            except Exception as e:
                traceback.print_exc()
                raise RuntimeError("Unable to copy config/example_permissions.ini to %s: %s" % (config_file, e))

        self.defaultGroup = PermissionGroup('Default', self.config['Default'])
        self.groups = set()

        for section in self.config.sections():
            self.groups.add(PermissionGroup(section, self.config[section]))

        # Create a fake section to fallback onto the permissive default values to grant to the owner
        ownerGroup = PermissionGroup("Owner (auto)", configparser.SectionProxy(self.config, None))
        if hasattr(grantAll, '__iter__'):
            ownerGroup.user_list = set(grantAll)

        self.groups.add(ownerGroup)
