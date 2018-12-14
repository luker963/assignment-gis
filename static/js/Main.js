L.mapbox.accessToken = 'pk.eyJ1IjoibHVrYXMtbWFkemlrIiwiYSI6ImNqbjRvczFtYTA2cmczcG1pbjU1cHFwcmsifQ.A5resbaC3BNaY_gXJMBN6w';
map = L.mapbox.map('map').setView([48.149784, 17.120030], 12)
    .addLayer(L.mapbox.tileLayer('mapbox.streets'));

var markers_services = [];

async function show_near_road(all_data) {
    all_data.forEach(function (data) {
            try {
                var d = "";

                if (data.properties.f1 !== null) {
                    d += " " + data.properties.f1;
                }
                var description = '<div>' + d + '</div>';
                marker = L.geoJson(data.geometry).bindPopup(description).addTo(map);
                marker.setStyle({
                    color: '#ff151c',
                    weight: 5
                });
                markers_services.push(marker);
            } catch (err) {
                console.error(err);
            }
        })
}

async function show_near_bus(all_data, remove, mrkr) {
    if (remove === true) {
        markers_services.forEach(function (e) {
            if (mrkr.latlng !== e._latlng) {
                e.remove()
            }
        });
        all_data.forEach(function (data) {
            try {
                var lat = parseFloat(data.geometry.coordinates[1]);
                var long = parseFloat(data.geometry.coordinates[0]);
                var color = '#4dff00';
                var icon = 'bus';
                var d = "";

                if (data.properties.f1 !== null) {
                    d += " " + data.properties.f1;
                }
                var description = '<div>' + d + '</div>';
                marker = L.marker([lat, long], {
                    icon: L.mapbox.marker.icon({
                        'marker-size': 'medium',
                        'marker-symbol': icon,
                        'marker-color': color
                    }),
                    'properties': data.properties
                }).bindPopup(description).addTo(map);
                markers_services.push(marker);
            } catch (err) {
                console.error(err);
            }
        })
    }

}

async function show_all(all_data, type, remove) {
    if (remove === true) {
        markers_services.forEach(function (e) {
            e.remove()
        });
        markers_services = [];
    }
    try {
        all_data.forEach(function (data) {
            try {
                var lat = parseFloat(data.geometry.coordinates[1]);
                var long = parseFloat(data.geometry.coordinates[0]);

                var color = '#272fff';
                var icon = 'lodging';
                var d = "";

                if (data.properties.f1 !== null) {
                    d += " " + data.properties.f1;
                }
                var description = '<div> ' +
                    '<p>' + d +
                    '</div>';

                marker = L.marker([lat, long], {
                    icon: L.mapbox.marker.icon({
                        'marker-size': 'medium',
                        'marker-symbol': icon,
                        'marker-color': color
                    }),
                    'properties': data.properties
                }).bindPopup(description).addTo(map);
                marker.on('click', function (mrkr) {
                    console.log(lat);
                    console.log(long);
                    var dis = 500;
                    var parks = $.getJSON('http://127.0.0.1:5000/get_near_bus/' + lat + '/' + long + '/', function (e) {
                        show_near_bus(e[0][0].features, true, mrkr);
                    });

                    $.when(parks).done(function () {
                        var road = $.getJSON('http://127.0.0.1:5000/get_near_road/' + lat + '/' + long + '/', function (e) {
                            show_near_road(e[0][0].features);
                        });
                    });
                });
                markers_services.push(marker);

            } catch (err) {
                console.error(err);
            }
        });
        map.addLayer(markers_services);
    } catch (error) {

    }
}

async function show_all_pamiatky(all_data, type, remove) {
    if (remove === true) {
        markers_services.forEach(function (e) {
            e.remove()
        });
        markers_services = [];
    }
    try {
        all_data.forEach(function (data) {
            try {
                var lat = parseFloat(data.geometry.coordinates[1]);
                var long = parseFloat(data.geometry.coordinates[0]);

                var color = '#272fff';
                var icon = 'star';
                var d = "";

                if (data.properties.f1 !== null) {
                    d += " " + data.properties.f1;
                }
                var description = '<div> ' +
                    '<p>' + d +
                    '</div>';

                marker = L.marker([lat, long], {
                    icon: L.mapbox.marker.icon({
                        'marker-size': 'medium',
                        'marker-symbol': icon,
                        'marker-color': color
                    }),
                    'properties': data.properties
                }).bindPopup(description).addTo(map);
                marker.on('click', function (mrkr) {
                    console.log(lat);
                    console.log(long);
                    var dis = 500;
                    var parks = $.getJSON('http://127.0.0.1:5000/get_near_bus2/' + lat + '/' + long + '/', function (e) {
                        show_near_bus(e[0][0].features, true, mrkr);
                    });
                    $.when(parks).done(function () {

                    })
                });
                markers_services.push(marker);
                //markers_services.addLayer(marker);

            } catch (err) {
                console.error(err);
            }
        });
        map.addLayer(markers_services);
    } catch (error) {

    }
}

function show_hotels_prices() {
    $.getJSON('http://127.0.0.1:5000/get_all_hotels_prices/', function (data) {
        markers_services.forEach(function (e) {
            e.remove()
        });
        markers_services = [];
        colors =[
            '#fff7f3',
            '#fde0dd',
            '#fcc5c0',
            '#fa9fb5',
            '#f768a1',
            '#dd3497',
            '#ae017e',
            '#7a0177',
            '#760473',
            '#49006a'];
        data.sort(function (a, b) {
            return a[1] - b[1];
        });
        var max = data[data.length-1][1];
        var min = data[0][1];
        var step = (max-min)/9;
        var curStep = 0;
        data.forEach(function (row, data) {
            var description = '<div> ' +
                        '<p>Name: ' + row[0] + '<p>' +
                        'Price: ' + row[1] +
                        '</div>';
            var ddd = L.geoJson(JSON.parse(row[2]));
                // ddd._layers = data[0];
            ddd.setStyle({
                fillColor: colors[curStep],
                // color: '#5270ff',
                fillOpacity: 0.9,
                weight: 0.8
            }).bindPopup(description);
            ddd.on('mouseover', function (e) {
                e.layer.openPopup(description);
            });
            ddd.on('mouseout', function (e) {
                e.layer.closePopup(description);
            });
            ddd.addTo(map);
            console.log(curStep);
            if(row[1] > min+(step*curStep+1)) {
                curStep++;
            }
            markers_services.push(ddd)
        })
    });
}

function hotels() {
    $.getJSON('http://127.0.0.1:5000/get_all_hotels/', function (e) {
        show_all(e[0][0].features, 1, true);
    });
}

function pamiatky() {
    $.getJSON('http://127.0.0.1:5000/get_all_pamiatky/', function (e) {
        show_all_pamiatky(e[0][0].features, 1, true);
    });
}