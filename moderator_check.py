import config
def user_is_moderator_or_higher(member_roles: list[object]):
    mod_or_higher_roles = []
    mod_role_id = mod_or_higher_roles.append(config.discord_bot_credentials["Server_Mod_Role_ID"])
    botmod_role_id = mod_or_higher_roles.append(config.discord_bot_credentials["Server_Botmod_Role_ID"])
    admin_role_id = mod_or_higher_roles.append(config.discord_bot_credentials["Server_Admin_Role_ID"])

    # My great pyramid of for loops! (hahaha)
    for role_id in mod_or_higher_roles:
        for role in member_roles:
            if role_id == role.id:
                return True