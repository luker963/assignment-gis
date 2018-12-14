import json

import numpy
import psycopg2 as psycopg2


class DbConn:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(host="localhost", database="template_postgis", user="postgres", password="123")
            self.cursor = self.conn.cursor()
            print("Connected")
        except Exception as e:
            print('Can not connect ', e)

    def generate_all_hotels_for_prices(self):
        self.cursor.execute("""
            SELECT 
                row_to_json((osm_id,
                name,
                way))
            FROM planet_osm_point
            WHERE (tourism='hotel');""")
        list_schemas = self.cursor.fetchall()
        for item in list_schemas:
            item[0]['f4'] = (numpy.random.normal()+2)*50+20
            sql = """
            INSERT INTO "hotel-prices"(
                osm_id, 
                name, 
                way, 
                price)
            VALUES (%s, %s, %s, %s);"""
            self.cursor.execute(sql, (item[0]['f1'], item[0]['f2'], item[0]['f3'], ((numpy.random.normal()+2)*50+20)))
        list_schemas = self.conn.commit()
        print("")


    def get_all_hotels(self):
        self.cursor.execute("""SELECT row_to_json(fc) FROM (
            SELECT
                'FeatureCollection' As type,
                array_to_json(array_agg(f)) As features
            FROM (
                SELECT 
                    'Feature' As type, 
                    ST_AsGeoJSON(way)::json As geometry, 
                    row_to_json((name, tourism)) As properties
                FROM planet_osm_point As lg
                WHERE (tourism='hotel')
            ) As f
        )  As fc;""")

        list_schemas = self.cursor.fetchall()
        return json.dumps(list_schemas)

    def get_all_hotels_prices(self):
        self.cursor.execute("""SELECT 
                pol.name, 
                AVG(poin.price),
                ST_AsGeoJSON(pol.way::geography) as geo
            FROM planet_osm_polygon pol, "hotel-prices" poin  
            WHERE pol.boundary like 'administrative'
                and pol.admin_level = '10'
                and pol.name != '500 bytov'
                and pol.name != 'Ahoj'
                and ST_Contains(pol.way, poin.way)
            GROUP BY pol.name, geo;""")

        list_schemas = self.cursor.fetchall()
        return json.dumps(list_schemas)

    def get_near_bus(self, lat, lon):
        self.cursor.execute("""SELECT row_to_json(fc) FROM ( 
            SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (
                SELECT 'Feature' As type, 
                    ST_AsGeoJSON(way)::json As geometry, 
                    row_to_json((name, highway)) As properties
                FROM planet_osm_point  As lg 
                WHERE ST_Dwithin(way, ST_GeogFromText('POINT(""" + lon + " " + lat + """)'), 500)and (highway='bus_stop')
            ) As f 
        ) As fc;""")

        list_schemas = self.cursor.fetchall()
        return json.dumps(list_schemas)

    def get_all_pamiatky(self):
        self.cursor.execute("""SELECT row_to_json(fc) FROM (
            SELECT
                'FeatureCollection' As type,
                array_to_json(array_agg(f)) As features
            FROM (
                SELECT 'Feature' As type, 
                    ST_AsGeoJSON(way)::json As geometry, 
                    row_to_json((name, historic)) As properties
                FROM planet_osm_point As lg
                WHERE (historic!='boundary_stone') AND (historic!='yes') AND (name!='null')
            ) As f
        )  As fc;""")

        list_schemas = self.cursor.fetchall()
        return json.dumps(list_schemas)

    def get_near_bus2(self, lat, lon):
        self.cursor.execute("""SELECT row_to_json(fc) FROM ( 
            SELECT
                'FeatureCollection' As type,
                array_to_json(array_agg(f)) As features
            FROM (
                select 
                    geometry,
                    row_to_json((name, highway)) As properties
                from (
                    select
                        *,
                        ROW_NUMBER() OVER (PARTITION BY t.name order by t.st_distance) AS r
                    from (
                        SELECT 
                            ST_AsGeoJSON(way)::json As geometry,
                            name,
                            highway,
                            st_distance(way, ST_GeogFromText('POINT(""" + lon + " " + lat + """)'))
					    FROM planet_osm_point As lg
					    WHERE ST_Dwithin(way, ST_GeogFromText('POINT(""" + lon + " " + lat + """)'), 1000) and (highway='bus_stop')
					) t
				) tt
				where tt.r=1
				order by tt.st_distance
				LIMIT 2 
			) As f 
		)  As fc;""")

        list_schemas = self.cursor.fetchall()
        return json.dumps(list_schemas)

    def get_near_road(self, lat, lon):
        self.cursor.execute("""SELECT row_to_json(fc) FROM ( 
            SELECT 
                'FeatureCollection' As type,
                array_to_json(array_agg(f)) As features
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
	        ) As f 
	    )  As fc;""")

        list_schemas = self.cursor.fetchall()
        return json.dumps(list_schemas)

