import shutil
import configparser

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
            ownerGroup.userList = set(grantAll)

        self.groups.add(ownerGroup)

    def forUser(self, user):
        """
        Returns the first PermissionGroup a user belongs to
        :param user: A discord User or Member object
        """

        for group in self.groups:
            if user.id in group.userList:
                return group

        # The only way I could search for roles is if I add a `server=None` param and pass that too
        if type(user) == discord_User:
            return self.default_group

        # We loop again so that we don't return a role based group before we find an assigned one
        for group in self.groups:
            for role in user.roles:
                if role.id in group.granted_to_roles:
                    return group

        return self.default_group

class PermissionGroup:
    def __init__(self, name, section_data):
        self.name = name

        self.commandWhitelist = section_data.get('CommandWhiteList', fallback=PermissionsDefaults.CommandWhiteList)
        self.commandBlacklist = section_data.get('CommandBlackList', fallback=PermissionsDefaults.CommandBlackList)
        self.grantedToRoles = section_data.get('GrantToRoles', fallback=PermissionsDefaults.GrantToRoles)
        self.userList = section_data.get('UserList', fallback=PermissionsDefaults.UserList)

        self.validate()

    def validate(self):
        if self.commandWhitelist:
            self.commandWhitelist = set(self.commandWhitelist.lower().split())

        if self.commandBlacklist:
            self.commandBlacklist = set(self.commandBlacklist.lower().split())

        if self.grantedToRoles:
            self.grantedToRoles = set(self.grantedToRoles.split())

        if self.userList:
            self.userList = set(self.userList.split())
