import time

from utils.assert_equals import assert_eq


def test_sql_attack(event_handler, sql, operation):
    time.sleep(5)  # Wait for attack to be reported
    attacks = event_handler.fetch_attacks()

    assert_eq(len(attacks), equals=1)
    attack = attacks[0]["attack"]

    # Test both attacks together :
    assert_eq(val1=attack["blocked"], equals=True)
    assert_eq(val1=attack["kind"], equals="sql_injection")
    assert_eq(val1=attack["metadata"], equals={'sql': sql})
    assert_eq(val1=attack["pathToPayload"], equals='.dog_name')
    assert_eq(val1=attack["payload"], equals="\"Dangerous Bobby', TRUE); -- \"")
    assert_eq(val1=attack["source"], equals="body")
    assert_eq(attack["operation"], equals=operation)

    # Test user :
    assert_eq(attack["user"]["id"], equals="user123")
    assert_eq(attack["user"]["id"], equals="John Doe")
