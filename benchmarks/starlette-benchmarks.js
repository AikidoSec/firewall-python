import http from 'k6/http';
import { check, sleep, fail } from 'k6';
import exec from 'k6/execution';
import { Trend } from 'k6/metrics';

const BASE_URL_8086 = 'http://localhost:8102';
const BASE_URL_8087 = 'http://localhost:8103';

export const options = {
    vus: 1, // Number of virtual users
    thresholds: {
        test_40mb_payload: [{
            threshold: "avg<15", // This is a higher threshold due to the data being processed
            abortOnFail: true,
            delayAbortEval: '10s',
        }],
        test_create_with_big_body: [{
            threshold: "avg<5", 
            abortOnFail: true,
            delayAbortEval: '10s',
        }],
        test_normal_route: [{
            threshold: "avg<5", 
            abortOnFail: true,
            delayAbortEval: '10s',
        }],
        test_id_route: [{
            threshold: "avg<5", 
            abortOnFail: true,
            delayAbortEval: '10s',
        }],
    },
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
    let long_text = "b".repeat(sizeInBytes)
    return {
        dog_name: "test",
        long_texts: new Array(1024).fill(long_text)
    }
}

function measureRequest(url, method = 'GET', payload, status_code=200, headers=default_headers) {
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
        'status is correct': (r) => r.status === status_code,
    });
    return res.timings.duration; // Return the duration of the request
}

function route_test(trend, amount, route, method="GET", data=default_payload, status=200) {
    for (let i = 0; i < amount; i++) {
        let time_with_fw = measureRequest(BASE_URL_8086 + route, method, data, status)
        let time_without_fw = measureRequest(BASE_URL_8087 + route, method, data, status)
        trend.add(time_with_fw - time_without_fw)
    }
}

export function handleSummary(data) {
    for (const [metricName, metricValue] of Object.entries(data.metrics)) {
        if(!metricName.startsWith('test_') || metricValue.values.avg == 0) {
            continue
        }
        let values = metricValue.values
        console.log(`🚅 ${metricName}: ΔAverage is ${values.avg.toFixed(2)}ms | ΔMedian is ${values.med.toFixed(2)}ms.`);
    }
    return {stdout: ""};
}

let test_40mb_payload = new Trend('test_40mb_payload')
let test_create_with_big_body = new Trend("test_create_with_big_body")
let test_normal_route = new Trend("test_normal_route")
let test_id_route = new Trend("test_id_route")
export default function () {
    route_test(test_40mb_payload, 30, "/create", "POST", generateLargeJson(40)) // 40 Megabytes
    route_test(test_create_with_big_body, 500, "/create", "POST")
    route_test(test_normal_route, 500, "/")
    route_test(test_id_route, 500, "/dogpage/1")
}
