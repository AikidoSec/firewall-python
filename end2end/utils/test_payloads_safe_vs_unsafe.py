from . import assert_eq

def test_payloads_safe_vs_unsafe(payloads, urls):
    if payloads["safe"]:
        print("Safe req to : (1) " + urls["enabled"] + payloads["safe"].route)
        assert_eq(val1=payloads["safe"].execute(urls["enabled"]), equals=200)
        print("Safe req to : (0) " + urls["disabled"] + payloads["safe"].route)
        assert_eq(val1=payloads["safe"].execute(urls["disabled"]), equals=200)
    if payloads["unsafe"]:
        print("Unsafe req to : (1) " + urls["enabled"] + payloads["unsafe"].route)
        assert_eq(val1=payloads["unsafe"].execute(urls["enabled"]), equals=500)
        print("Unsafe req to : (0) " + urls["disabled"] + payloads["unsafe"].route)
        assert_eq(val1=payloads["unsafe"].execute(urls["disabled"]), equals=200)
