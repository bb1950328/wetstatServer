class CSV {
    data = [];
    heads = [];

    constructor(string_data = null) {
        if (string_data != null) {
            let first = true;
            string_data.split("\n").forEach(line => {
                let line_obj = [];
                line.split(";").forEach(cell => {
                    line_obj.push(cell.replace("\r", "").replace("\n", ""));
                });
                if (first) {
                    first = false;
                    this.heads = line_obj;
                } else {
                    this.data.push(line_obj);
                }
            });
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

function update_last_refresh() {
    let last_refreshed = document.getElementById("last-refreshed");
    if (last_refreshed !== null) {
        let today = new Date();
        // todo check if it's really locale format
        last_refreshed.innerText = today.toLocaleDateString() + " " + today.toLocaleTimeString();
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
                callback(result)
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

$("document").ready(function () {
    $("header").load("header.html");
    $("footer").load("footer.html?y=z", () => update_last_refresh());
});
