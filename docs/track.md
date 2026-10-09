# Track custom events

Use `track()` to report events that only your application knows about, such as failed logins. [Playbooks](https://help.aikido.dev/zen-firewall/zen-features/playbooks) can act when an event occurs repeatedly, for example by blocking an IP after three failed logins in five minutes.

```python
from aikido_zen import set_user, track

@app.route("/login", methods=["POST"])
def login():
    user = authenticate(request.form["username"], request.form["password"])

    if not user:
        track("user.login_failed")
        return {"error": "Invalid credentials"}, 401

    set_user({"id": user.id})
    track("user.login_succeeded")
    return {"token": create_token(user)}
```

After adding `track()`, trigger the event at least once. It will then appear on the Playbooks page in the Aikido dashboard. From there, you can create a playbook and choose what should happen when the event occurs. Calling `track()` by itself does not create a playbook or block anything.

Call `track()` while handling an HTTP request. Zen associates the event with the request's IP address. Playbook counts are per IP, not across your whole app. If you call [`set_user()`](./user.md) before `track()`, Zen also includes the current user. `set_user()` is optional. Events without a user are still tracked.

Event names can use any format. We recommend lowercase, dot-separated names such as `user.login_failed`.
