class Users:
    def __init__(self, max_entries=1000):
        self.max_entries = max_entries
        self.users = {}

    def add_user(self, user_id, user_name, user_ip, current_time):
        self.ensure_max_entries()

        first_seen_at = current_time
        if self.users.get(user_id):
            # Use the first_seen_at timestamp of the existing user
            first_seen_at = self.users.get(user_id).get("firstSeenAt")

        self.users[user_id] = {
            "id": user_id,
            "name": user_name,
            "lastIpAddress": user_ip,
            "firstSeenAt": first_seen_at,
            "lastSeenAt": current_time,
        }

    def add_user_from_entry(self, user_entry):
        self.ensure_max_entries()

        existing_user = self.users.get(user_entry["id"])
        if existing_user:
            # Use the firstSeenAt timestamp of the existing user
            user_entry["firstSeenAt"] = existing_user["firstSeenAt"]

        self.users[user_entry["id"]] = user_entry

    def ensure_max_entries(self):
        if len(self.users) >= self.max_entries:
            # Remove the first added user (FIFO)
            first_added_key = next(iter(self.users))
            del self.users[first_added_key]

    def as_array(self):
        return [dict(user) for user in self.users.values()]

    def clear(self):
        self.users.clear()
