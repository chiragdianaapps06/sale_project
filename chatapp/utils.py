def get_private_group_name(self, user1, user2):
    usernames = sorted([user1.username, user2.username])
    return f"private_chat_{usernames[0]}_{usernames[1]}"