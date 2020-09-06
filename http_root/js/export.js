function start_export() {
    let startDate = document.getElementById("input_start_date").valueAsDate;
    let endDate = document.getElementById("input_end_date").valueAsDate;
    let startTs = startDate.getTime() / 1000;
    let endTs = endDate.getTime() / 1000;
    let interval = document.getElementById("input_interval").value;
    let tmpElement = document.createElement("a");
    tmpElement.setAttribute("href", get_values_url(startTs, endTs, interval));
    tmpElement.setAttribute("target", "_blank");
    let filename = "wetstat_" + format_filename_date(startDate) + "_to_" + format_filename_date(endDate) + "_" + interval + ".csv";
    tmpElement.setAttribute("download", filename)
    document.body.appendChild(tmpElement);
    tmpElement.click();
    document.body.removeChild(tmpElement);
}

function format_filename_date(date) {
    return date.toLocaleDateString("de-CH").replaceAll(".", "_");
}
