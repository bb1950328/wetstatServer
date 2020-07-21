let wp;
let debug = true;
document.addEventListener("DOMContentLoaded", function (event) {
    let now = unix_now();
    if (debug) {
        now -= 60 * 60 * 24 * 30;
    }
    let start = now - 60 * 60 * 24 * 2;
    get_values(start, now, csv => {
        let data = new WetplotData(csv.heads, csv.data);
        wp = new Wetplot();
        //wp._addDataToDb("10min", data);
        wp._data = data;
        wp.config("height", window.innerHeight * 0.7);
        wp.config("background_color", "#ffffff");
        wp.config("hover_box_background_color", "#bbbbbb");
        wp.config("time_offset", start);

        get_sensors(sensors => {
            for (const sens_info of sensors) {
                let short_name = sens_info["short_name"];
                console.debug(short_name);
                let col_index = csv.heads.indexOf(short_name);
                if (col_index === -1 || !csv.data[0][col_index]) {
                    continue;
                }
                wp.addLine(short_name);
                wp.lineConfig(short_name, "name", sens_info["name"]);
                wp.lineConfig(short_name, "unit", sens_info["unit"]);
                wp.lineConfig(short_name, "color", sens_info["color"]);
                wp.lineConfig(short_name, "auto_min_max", true);
            }
            wp.initialize();
            wp.scrollTo(10000000000000000000000000);
        });
    });
});
