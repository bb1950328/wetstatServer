function create_sensor_divs() {
    get_sensors(sensors => {
        let container = document.getElementById("sensor-values-container");
        let template = $(".sensor-value-div.template").html().toString();
        sensors.forEach(sens_info => {
            let html = template.replace("%%sensor_name%%", sens_info["name"]);
            let elem = document.createElement("div");
            elem.classList.add("sensor-value-div");
            elem.id = "valueDiv" + sens_info["short_name"];
            elem.style.backgroundColor = sens_info["color"];
            elem.innerHTML = html;
            container.appendChild(elem);
        });
        fill_current_values();
    });
}

function fill_current_values() {
    get_current_values((csv) => {
        csv.heads.forEach(short_name => {
            get_sensor_unit(short_name, unit => {
                let value = csv.getCell(short_name);
                $("#valueDiv" + short_name + " .sensor-value").text(value + " " + unit);
            });
        });
    });
    let now = unix_now();
    [["24h", 86400], ["28d", 2419200], ["1y", 31536000]].forEach(_x => {
        let [class_suffix, seconds] = _x;
        get_next_value(now - seconds, csv => {
            csv.heads.forEach(short_name => {
                get_sensor_unit(short_name, unit => {
                    let value = csv.getCell(short_name);
                    $("#valueDiv" + short_name + " .before-value.before" + class_suffix).text(value + " " + unit);
                });
            });
        })
    })
    setTimeout(fill_current_values, 10000);
    update_last_refresh();
}

$("document").ready(function () {
    create_sensor_divs();
});
