class CSV {
    data = [];
    heads = [];

    constructor(string_data = null) {
        if (string_data != null) {
            let first = true;
            for (const line of string_data.split("\n")) {
                let line_obj = [];
                for (let i = 0; i < line.split(";").length; i++) {
                    let cell = line.split(";")[i];
                    cell = cell.replace("\r", "").replace("\n", "");
                    let asFloat = Number.parseFloat(cell);
                    if (!isNaN(asFloat)) {
                        cell = asFloat;
                    }
                    line_obj.push(cell);
                }
                if (first) {
                    first = false;
                    this.heads = line_obj;
                } else {
                    this.data.push(line_obj);
                }
            }
        }
    }

    getCell(column, rowIndex = 0) {
        if (typeof column === typeof "") {
            column = this.heads.indexOf(column);
        }
        return this.data[rowIndex][column];
    }

    getCellMap(rowIndex = 0) {
        let res = {};
        for (let column = 0; column < this.heads.length; column++) {
            res[this.heads[column]] = this.data[rowIndex][column];
        }
        return res;
    }

    forEach(rowIndex, callback) {
        if (rowIndex instanceof Number) {
            callback(this.data[rowIndex]);
        } else if (rowIndex instanceof Array) {
            rowIndex.forEach(row => callback(this.data[row]));
        } else {
            for (let row = 0; row < this.data.length; row++) {
                callback(this.data[row]);
            }
        }
    }
}

/**
 * @returns {number} unix timestamp in seconds
 */
function unix_now() {
    return Math.floor(Date.now() / 1000)
}

function update_last_refresh() {
    let last_refreshed = document.getElementById("last-refreshed");
    if (last_refreshed !== null) {
        let today = new Date();
        last_refreshed.innerText = today.toLocaleString();
    }
}

let _get_sensors_result = null;

function get_sensors(callback) {
    if (_get_sensors_result !== null) {
        callback(_get_sensors_result);
    } else {
        $.ajax({
            url: "api/sensors",
            type: "get",
            success: (result, status, xhr) => {
                _get_sensors_result = result;
                callback(result);
            },
        });
    }
}

function get_sensor_unit(short_name, callback) {
    get_sensors(sensor_info => {
        for (let i = 0; i < sensor_info.length; i++) {
            if (sensor_info[i]["short_name"] === short_name) {
                callback(sensor_info[i]["unit"]);
            }
        }
    })
}

function get_current_values(callback) {
    $.ajax({
        url: "api/current_values",
        type: "get",
        success: (result, status, xhr) => {
            callback(new CSV(result));
        },
    });
}

function get_next_value(to, callback) {
    $.ajax({
        url: "api/next_value?to=" + to,
        type: "get",
        success: (result, status, xhr) => {
            callback(new CSV(result));
        },
    });
}

function get_values_url(from, to, interval) {
    if (to === -1) {
        to = unix_now();
    }
    if (from === -1) {
        from = to - 24 * 60 * 60;
    }
    return "api/values?to=" + to + "&from=" + from + "&interval=" + interval;
}

function get_values(from = -1, to = -1, interval, callback) {
    const url = get_values_url(from, callback, to);
    console.log(url);
    $.ajax({
        url: url,
        type: "get",
        success: (result, status, xhr) => {
            callback(new CSV(result));
        },
    });
}

$("document").ready(function () {
    $("header").load("header.html");
    $("footer").load("footer.html?y=z", () => update_last_refresh());
});
