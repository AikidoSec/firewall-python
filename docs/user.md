# Setting the current user

To set the current user, you can use the `setUser` function.

```python
from aikido_zen import set_user

# Set a user (presumably in middleware) :
set_user({"id": "123", "name": "John Doe"})
```

Using `set_user` has the following benefits:

- The user ID is used for more accurate rate limiting (you can change IP addresses, but you can't change your user ID).
- Whenever attacks are detected, the user will be included in the report to Aikido.
- The dashboard will show all your users, where you can also block them.
- Passing the user's name is optional, but it can help you identify the user in the dashboard. You will be required to list Aikido Security as a subprocessor if you choose to share personal identifiable information (PII).

# Rate limiting groups

To limit the number of requests for a group of users, you can use the `set_rate_limit_group` function. For example, this is useful if you want to limit the number of requests per team or company.
Please note that if a rate limit group is set, the configured rate limits are only applied to the group and not to individual users or IP addresses.

```python
from aikido_zen import set_rate_limit_group

set_rate_limit_group("id_of_group");
```

## Framework configuration

- [Django](./django.md#rate-limiting-and-user-blocking)
- [Flask](./flask.md#rate-limiting-and-user-blocking)
- [Quart](./quart.md#rate-limiting-and-user-blocking)
- [Starlette](./starlette.md#rate-limiting-and-user-blocking)
- [FastAPI](./fastapi.md#rate-limiting-and-user-blocking)
