# Tracking events

`track` lets you record things happening in your app — like failed logins, signups, or password resets. Zen sends these to Aikido so patterns can be detected, like someone failing to log in 50 times in a minute.

```python
from aikido_zen import track, set_user

def login(request):
    user = authenticate(request)

    if not user:
        track("user.login_failed")
        return unauthorized_response()

    set_user({"id": user.id})
    track("user.login_succeeded")
    return success_response()
```

Zen automatically picks up the IP address, user agent, and current user (if you called [`set_user`](./user.md)) from the request — you don't need to pass those yourself.

## More examples

```python
track("user.signed_up")
track("user.password_reset_requested")
track("plan.invite_sent")
track("payment.failed")
```

## Naming events

Use lowercase with dots to group related events:

- `user.login_failed`
- `user.login_succeeded`
- `user.signed_up`
- `user.password_reset_requested`
- `payment.failed`
- `plan.invite_sent`

## Things to know

`track` only works inside an HTTP request. If you call it in a background job or a script, nothing gets sent and you'll see a warning in the console.

If you haven't called `set_user` yet, the event still goes through — it just won't have a user ID attached.
