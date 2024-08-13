import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL_8086 = 'http://localhost:8086';
const BASE_URL_8087 = 'http://localhost:8087';

export const options = {
    vus: 1, // Number of virtual users
};
const default_headers = {
    "User-Agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
};

const default_payload = {
    dog_name: "Pops",
    other_dogs: Array(2000).fill("Lorem Ipsum"),
    other_dogs2: Array.from({length: 5000}, () => Math.floor(Math.random() * 99999999)),
    text_message: "Lorem ipsum dolor sit amet".repeat(3000)

};
function generateLargeJson(sizeInMB) {
    const sizeInBytes = sizeInMB * 1024; // Convert MB to Kilobytes
    let currentSize = 0;
    let long_text = "b".repeat(sizeInBytes)
    return {
        dog_name: "test",
        long_texts: new Array(1024).fill(long_text)
    }
}
function calculateMedian(arr) {
    if (arr.length === 0) return null; // Handle empty array case

    const sortedArr = arr.slice().sort((a, b) => a - b); // Sort the array
    const mid = Math.floor(sortedArr.length / 2);

    if (sortedArr.length % 2 === 0) {
        // If even, return the average of the two middle numbers
        return (sortedArr[mid - 1] + sortedArr[mid]) / 2;
    } else {
        // If odd, return the middle number
        return sortedArr[mid];
    }
}

function measureRequest(url, method = 'GET', payload, headers=default_headers) {
    let res;
    if (method === 'POST') {
        res = http.post(url, payload, {
            headers: headers
        }
        );
    } else {
        res = http.get(url, {
            headers: headers
        });
    }
    check(res, {
        'status is 200': (r) => r.status === 200,
    });
    return res.timings.duration; // Return the duration of the request
}
function route_test(amount, route, method="GET", data=default_payload) {
    let time_in_mss_8086 = []
    let time_in_mss_8087 = []
    for (let i = 0; i < amount; i++) {
        time_in_mss_8086.push(measureRequest(BASE_URL_8086 + route, method, data));
        time_in_mss_8087.push(measureRequest(BASE_URL_8087 + route, method, data));
    }
    return {
        median_without_fw: calculateMedian(time_in_mss_8087),
        median_with_fw: calculateMedian(time_in_mss_8086),
        avg_without_fw: time_in_mss_8087.reduce((acc, num) => acc + num, 0)/amount,
        avg_with_fw: time_in_mss_8086.reduce((acc, num) => acc + num, 0)/amount
    }
}
function log_test_results(test, res) {
    let avg_delta = res.avg_with_fw - res.avg_without_fw
    let median_delta = res.median_with_fw - res.median_without_fw
    console.log(`\x1b[35m 🚅 ${test}\x1b[0m: ΔAverage is \x1b[4m${avg_delta.toFixed(2)}ms\x1b[0m | ΔMedian is \x1b[4m${median_delta.toFixed(2)}ms\x1b[0m`)
}
export default function () {
    console.log("======  Benchmarking results: ======")
    route_test(1, "/create", "POST", generateLargeJson(40)) // Cold-Turkey
    const res_40mb = route_test(10, "/create", "POST", generateLargeJson(40)) // 40 Megabytes
    log_test_results("Test a 40MB payload on /create", res_40mb)

    const res_multi_no_bb = route_test(50, "/multiple_queries", "POST", {dog_name: "W"})
    log_test_results("Testing with execution of multiple SQL queries", res_multi_no_bb)

    const res_multi_queries = route_test(50, "/multiple_queries", "POST")
    log_test_results("Testing with execution of multiple SQL queries and a big body", res_multi_queries)

    const res_bb_post = route_test(500, "/create", "POST")
    log_test_results("Posting with a big body on /create", res_bb_post)

    const res_normal_route = route_test(1000, "/")
    log_test_results("Testing normal route on /", res_normal_route)

    const res_id_route = route_test(500, "/dogpage/1")
    log_test_results("Testing ID'ed route on /dopgage/1", res_id_route)

    const res_open_file = route_test(500, "/open_file", 'POST', { filepath: '.env.example' })
    log_test_results("Test opening a file on /open_file", res_open_file)

    const res_execute_shell = route_test(500, "/shell", "POST", { command: 'xyzwh'})
    log_test_results("Test executing a command on /shell", res_open_file)
}
