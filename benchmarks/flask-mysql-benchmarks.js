import http from 'k6/http';
import { check, sleep, fail } from 'k6';
import exec from 'k6/execution';
import { Trend } from 'k6/metrics';

// Flask MySQL :
const BASE_URL_8086 = 'http://localhost:8086';
const BASE_URL_8087 = 'http://localhost:8087';

// Flask Mongo :
const BASE_URL_8094 = 'http://localhost:8094';
const BASE_URL_8095 = 'http://localhost:8095';


export const options = {
    vus: 1, // Number of virtual users
    thresholds: {
        test_40mb_payload: [{
            threshold: "avg<2000", // Temporary exagurated threshold until optimizations are finished 
            abortOnFail: true,
            delayAbortEval: '10s',
        }],
        test_multiple_queries: [{
            threshold: "avg<2000", 
            abortOnFail: true,
            delayAbortEval: '10s',
        }],
        test_multiple_queries_with_big_body: [{
            threshold: "avg<2000", 
            abortOnFail: true,
            delayAbortEval: '10s',
        }],
        test_create_with_big_body: [{
            threshold: "avg<2000", 
            abortOnFail: true,
            delayAbortEval: '10s',
        }],
        test_normal_route: [{
            threshold: "avg<2000", 
            abortOnFail: true,
            delayAbortEval: '10s',
        }],
        test_id_route: [{
            threshold: "avg<2000", 
            abortOnFail: true,
            delayAbortEval: '10s',
        }],
        test_open_file: [{
            threshold: "avg<2000", 
            abortOnFail: true,
            delayAbortEval: '10s',
        }],
        test_execute_shell: [{
            threshold: "avg<2000", 
            abortOnFail: true,
            delayAbortEval: '10s',
        }],
        test_nosql_query: [{
            threshold: "avg<2000", 
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

function measureRequest(url, method = 'GET', payload, status_code=200, headers=default_headers, json_body=false) {
    let res;
    if (method === 'POST') {
        if (json_body) {
            res = http.post(url, JSON.stringify(payload), {
                headers: { 'Content-Type': 'application/json' },
            })
        }
        else {
            res = http.post(url, payload, {
                headers: headers
            })
        };
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

function route_test(trend_avg, amount, route, method="GET", data=default_payload, status=200, trend_percentage=undefined) {
    for (let i = 0; i < amount; i++) {
        let time_with_fw = measureRequest(BASE_URL_8086 + route, method, data, status)
        let time_without_fw = measureRequest(BASE_URL_8087 + route, method, data, status)
        trend_avg.add(time_with_fw - time_without_fw)
        if (trend_percentage) {
            trend_percentage.add((time_with_fw - time_without_fw)/time_with_fw)
        }
    }
}

function route_test_mongo(trend_avg, amount, route, method="GET", data=default_payload, status=200, trend_percentage=undefined) {
    for (let i = 0; i < amount; i++) {
        let time_with_fw = measureRequest(BASE_URL_8094 + route, method, data, status, json_body=true)
        let time_without_fw = measureRequest(BASE_URL_8095 + route, method, data, status, json_body=true)
        trend_avg.add(time_with_fw - time_without_fw)
        if (trend_percentage) {
            trend_percentage.add((time_with_fw - time_without_fw)/time_with_fw)
        }
    }
}

export function handleSummary(data) {
    for (const [metricName, metricValue] of Object.entries(data.metrics)) {
        if(!metricName.startsWith('test_') || metricValue.values.avg == 0) {
            continue
        }
        let values = metricValue.values
        console.log(`\x1b[35m 🚅 ${metricName}\x1b[0m: ΔAverage is \x1b[4m${values.avg.toFixed(2)}ms\x1b[0m | ΔMedian is \x1b[4m${values.med.toFixed(2)}ms\x1b[0m`);
    }
    return {stdout: ""};
}

let test_40mb_payload = new Trend('test_40mb_payload')
let test_multiple_queries = new Trend("test_multiple_queries")
let test_multiple_queries_p = new Trend("p_test_multiple_queries")
let test_multiple_queries_with_big_body = new Trend("test_multiple_queries_with_big_body")
let test_create_with_big_body = new Trend("test_create_with_big_body")
let test_normal_route = new Trend("test_normal_route")
let test_normal_route_p = new Trend("p_test_normal_route")
let test_id_route = new Trend("test_id_route")
let test_open_file = new Trend("test_open_file")
let test_open_file_p = new Trend("p_test_open_file")
let test_execute_shell = new Trend("test_execute_shell")
let test_nosql_query = new Trend("test_nosql_query")
let test_nosql_query_p = new Trend("p_test_nosql_query")
export default function () {
    route_test(test_40mb_payload, 30, "/create", "POST", generateLargeJson(40)) // 40 Megabytes
    route_test(test_multiple_queries, 50, "/multiple_queries", "POST", {dog_name: "W"}, trend_percentage=test_multiple_queries_p)
    route_test(test_multiple_queries_with_big_body, 50, "/multiple_queries", "POST")
    route_test(test_create_with_big_body, 500, "/create", "POST")
    route_test(test_normal_route, 500, "/", trend_percentage=test_normal_route_p)
    route_test(test_id_route, 500, "/dogpage/1")
    route_test(test_open_file, 500, "/open_file", 'POST', { filepath: '.env.example' }, trend_percentage=test_open_file_p)
    route_test(test_execute_shell, 500, "/shell", "POST", { command: 'xyzwh'})

    route_test_mongo(test_nosql_query, 500, "/auth", "POST", {
        "dog_name": "doggo",
        "pswd": "Pswd123"
    }, trend_percentage=test_nosql_query_p)
}
