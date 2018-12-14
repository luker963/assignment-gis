# Overview

This application shows hotels and touristic attractions in Bratislava on a map. Most important features are:
- Show hotels / attractions
![Screenshot](Hotels.png)
![Screenshot](Pamiatky.png)
- Show nearest road and bus stations in 500m proximity of selected hotel
![Screenshot2](Hotels-detail.png)
- Show 2 nearest different-name bus stations to touristic attractions
![Screenshot4](Pamiatky-detail.png)
- Show heatmap of hotels price divided to city districts
![Screenshot3](Hotely-cena.png)


The application has 2 separate parts, the client which is a [frontend web application](#frontend) using mapbox API and mapbox.js and the [backend application](#backend) written in [Python](http://python.org/) framework [Flask](flask.pocoo.png), backed by PostGIS. The frontend application communicates with backend using a [REST API](#api).

# Frontend

The frontend application is a static HTML page (`index.html`), which shows a mapbox.js widget. It is displaying hotels, which are mostly in cities, thus the map style is based on the Emerald style. I modified the style to better highlight main sightseeing points, restaurants and bus stops, since they are all important when selecting a hotel. I also highlighted rails tracks to assist in finding a quiet location.

All relevant frontend code is in `Main.js` which is referenced from `index.html`. The frontend code is very simple, its only responsibilities are transforming query results to map on webpage.

# Backend

The backend application is written in python framework - flask and is responsible for querying geo data, formatting the geojson and data for the sidebar panel.

## Data

Hotel data is coming directly from Open Street Maps. I downloaded an extent covering Bratislava city and its surroundings (around 200MB) and imported it using the `osm2pgsql` tool into the PostGis database running in docker. I was not ale to find relevant prices of hotel accommodations, so I generated prices using gausian distribution and I inserted prices along with hotel name, id and geometry.

## Api

**Returns average hotel prices for heatmap**

`GET /get_all_hotels_prices/`

**Returns all hotels**

`GET /get_all_hotels/`

**Returns all bus stations in 500m distance**

`GET /get_near_bus/<lat>/<lon>/`

**Returns 2 different nearest bus stations in 1000m distance**

`GET /get_near_bus2/<lat>/<lon>/`

**Returns nearest road according to lon and lat coordinates**

`GET /get_near_road/<lat>/<lon>/`

**Returns all touristic attractions**

`GET /get_all_pamiatky/`

### Response

All API responses are in general the same structure:
```
[
    [
        "name": "Name of object",
        "way": geometry of object,
        "properties": some additional object properties
    ],
    [...],
    ...
]
```
### Querys

Every API request represents query executed in DB:

`/get_all_hotels_prices/`

```
SELECT 
    pol.name, 
    AVG(point.price),
    ST_AsGeoJSON(pol.way::geography) as geo
FROM planet_osm_polygon pol, "hotel-prices" point  
WHERE pol.boundary like 'administrative'
    and pol.admin_level = '10'
    and pol.name != '500 bytov'
    and pol.name != 'Ahoj'
    and ST_Contains(pol.way, point.way)
GROUP BY pol.name, geo;
```

Simple self-explaining query returning average price of hotels grouped by city districts.

Explain:
```
"GroupAggregate  (cost=3973.10..3973.13 rows=1 width=59)"
"  Group Key: pol.name, (_st_asgeojson(1, (pol.way)::geography, 15, 0))"
"  ->  Sort  (cost=3973.10..3973.11 rows=1 width=59)"
"        Sort Key: pol.name, (_st_asgeojson(1, (pol.way)::geography, 15, 0))"
"        ->  Nested Loop  (cost=0.00..3973.09 rows=1 width=59)"
"              Join Filter: ((pol.way ~ point.way) AND _st_contains(pol.way, point.way))"
"              ->  Seq Scan on planet_osm_polygon pol  (cost=0.00..3957.10 rows=1 width=199)"
"                    Filter: ((boundary ~~ 'administrative'::text) AND (name <> '500 bytov'::text) AND (name <> 'Ahoj'::text) AND (admin_level = '10'::text))"
"              ->  Seq Scan on "hotel-prices" point  (cost=0.00..1.55 rows=55 width=40)"
```

---------------------

`/get_all_hotels/`

```
SELECT row_to_json(b) FROM (
    SELECT
        array_to_json(array_agg(a)) As features
    FROM (
        SELECT 
            ST_AsGeoJSON(way)::json As geometry, 
            row_to_json((name, tourism)) As properties
        FROM planet_osm_point
        WHERE (tourism='hotel')
    ) As a
)  As b;
```

Query returns coordinates of all hotels along with hotel names.

Explain:
```
"Subquery Scan on b  (cost=1291.04..1291.06 rows=1 width=32)"
"  ->  Aggregate  (cost=1291.04..1291.05 rows=1 width=32)"
"        ->  Seq Scan on planet_osm_point  (cost=0.00..1125.38 rows=66 width=55)"
"              Filter: (tourism = 'hotel'::text)"
```

---------------------

`/get_near_bus/<lat>/<lon>/`

```
SELECT row_to_json(b) FROM ( 
    SELECT 
        array_to_json(array_agg(a)) As features 
        FROM (
            SELECT  
                ST_AsGeoJSON(way)::json As geometry, 
                row_to_json((name, highway)) As properties
            FROM 
                planet_osm_point
            WHERE 
                ST_Dwithin(way, ST_GeogFromText('POINT(""" + lon + " " + lat + """)'), 500) and (highway='bus_stop')
        ) As a 
    ) As b;
```

Query returns all bus stations near desired location (lat, lon) along with station names.

Explain:
```
"Subquery Scan on b  (cost=19743.65..19743.68 rows=1 width=32)"
"  ->  Aggregate  (cost=19743.65..19743.66 rows=1 width=32)"
"        ->  Seq Scan on planet_osm_point  (cost=0.00..19706.00 rows=15 width=55)"
"              Filter: ((highway = 'bus_stop'::text) AND ((way)::geography && '0101000020E6100000AB532F09610B3140F078495288194840'::geography) AND ('0101000020E6100000AB532F09610B3140F078495288194840'::geography && _st_expand((way)::geography, '500'::double precision)) AND _st_dwithin((way)::geography, '0101000020E6100000AB532F09610B3140F078495288194840'::geography, '500'::double precision, true))"
```


---------------------

`/get_near_bus2/<lat>/<lon>/`

```
SELECT row_to_json(d) FROM ( 
    SELECT
        array_to_json(array_agg(c)) As features
    FROM (
        select 
            geometry,
            row_to_json((name, highway)) As properties
        FROM (
            select
                *,
                ROW_NUMBER() OVER (PARTITION BY a.name order by a.st_distance) AS r
            FROM (
                SELECT 
                    ST_AsGeoJSON(way)::json As geometry,
                    name,
                    highway,
                    st_distance(way, ST_GeogFromText('POINT(""" + lon + " " + lat + """)'))
                FROM planet_osm_point As lg
                WHERE ST_Dwithin(way, ST_GeogFromText('POINT(""" + lon + " " + lat + """)'), 1000) and (highway='bus_stop')
            ) a
        ) b
        where b.r=1
        order by b.st_distance
        LIMIT 2 
    ) As c 
)  As d;
```

Query returns two nearest bus stations with different name in desired location. All bus stations in desired area (1km distance from requested lon / lat) are partitioned by their names and sorted by distance, then are top two stations selected by their first occurence in returned response.

Explain:
```
"Subquery Scan on d  (cost=19751.96..19751.99 rows=1 width=32)"
"  ->  Aggregate  (cost=19751.96..19751.98 rows=1 width=32)"
"        ->  Subquery Scan on c  (cost=19751.94..19751.96 rows=1 width=56)"
"              ->  Limit  (cost=19751.94..19751.95 rows=1 width=72)"
"                    ->  Sort  (cost=19751.94..19751.95 rows=1 width=72)"
"                          Sort Key: b.st_distance"
"                          ->  Subquery Scan on b  (cost=19710.08..19751.93 rows=1 width=72)"
"                                Filter: (b.r = 1)"
"                                ->  WindowAgg  (cost=19710.08..19751.74 rows=15 width=71)"
"                                      ->  Sort  (cost=19710.08..19710.12 rows=15 width=63)"
"                                            Sort Key: lg.name, (_st_distance((lg.way)::geography, '0101000020E6100000AB532F09610B3140F078495288194840'::geography, '0'::double precision, true))"
"                                            ->  Seq Scan on planet_osm_point lg  (cost=0.00..19709.79 rows=15 width=63)"
"                                                  Filter: ((highway = 'bus_stop'::text) AND ((way)::geography && '0101000020E6100000AB532F09610B3140F078495288194840'::geography) AND ('0101000020E6100000AB532F09610B3140F078495288194840'::geography && _st_expand((way)::geography, '1000'::double precision)) AND _st_dwithin((way)::geography, '0101000020E6100000AB532F09610B3140F078495288194840'::geography, '1000'::double precision, true))"
```


---------------------

`/get_near_road/<lat>/<lon>/`

```
SELECT row_to_json(b) FROM ( 
    SELECT 
        array_to_json(array_agg(a)) As features
    FROM (
        SELECT
            geometry,
            row_to_json((name, dist)) As properties
        FROM(
            SELECT
                name,
                ST_AsGeoJSON(way)::json As geometry,
                ST_Distance(way, ST_GeogFromText('POINT(""" + lon + " " + lat + """)'), false) AS dist
            FROM
                planet_osm_line
            WHERE z_order = 33 AND name != 'null' 
            )rs 
        ORDER BY dist
        LIMIT 1
    ) As a 
)  As b;
```

Query returns nearest road piece to desired location (lon / lat) with filled name and is in "roads order".

Explain:
```
"Subquery Scan on b  (cost=2497.39..2497.42 rows=1 width=32)"
"  ->  Aggregate  (cost=2497.39..2497.41 rows=1 width=32)"
"        ->  Subquery Scan on a  (cost=2494.35..2497.39 rows=1 width=24)"
"              ->  Limit  (cost=2494.35..2497.38 rows=1 width=72)"
"                    ->  Result  (cost=2494.35..5056.53 rows=847 width=72)"
"                          ->  Sort  (cost=2494.35..2496.47 rows=847 width=223)"
"                                Sort Key: (_st_distance((planet_osm_line.way)::geography, '0101000020E6100000AB532F09610B3140F078495288194840'::geography, '0'::double precision, false))"
"                                ->  Seq Scan on planet_osm_line  (cost=0.00..2490.12 rows=847 width=223)"
"                                      Filter: ((name <> 'null'::text) AND (z_order = 33))"
```


---------------------

`/get_all_pamiatky/`

```
SELECT row_to_json(b) FROM (
    SELECT
        'FeatureCollection' As type,
        array_to_json(array_agg(a)) As features
    FROM (
        SELECT 'Feature' As type, 
            ST_AsGeoJSON(way)::json As geometry, 
            row_to_json((name, historic)) As properties
        FROM planet_osm_point As lg
        WHERE (historic!='boundary_stone') AND (historic!='yes') AND (name!='null')
    ) As a
)  As b;
```

Query returns coordinates of all touristic attractions ('historic' field) along with their names.

Explain:
```
"Subquery Scan on b  (cost=1367.64..1367.66 rows=1 width=32)"
"  ->  Aggregate  (cost=1367.64..1367.65 rows=1 width=64)"
"        ->  Seq Scan on planet_osm_point lg  (cost=0.00..1365.12 rows=1 width=56)"
"              Filter: ((historic <> 'boundary_stone'::text) AND (historic <> 'yes'::text) AND (name <> 'null'::text))"
```

