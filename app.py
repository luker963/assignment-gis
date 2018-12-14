from flask import Flask, render_template

from DbConn import DbConn

app = Flask(__name__)

dbConn = DbConn()

@app.route('/')
def index():
    # dbConn.generate_all_hotels_for_prices()
    return render_template('index.html')

@app.route('/get_all_hotels_prices/', methods=['GET', 'POST'])
def get_all_hotels_prices():
    return dbConn.get_all_hotels_prices()

@app.route('/get_all_hotels/', methods=['GET', 'POST'])
def get_all_hotels():
    return dbConn.get_all_hotels()

@app.route('/get_near_bus/<lat>/<lon>/', methods=['GET', 'POST'])
def get_near_bus(lat, lon):
    return dbConn.get_near_bus(lat, lon)

@app.route('/get_near_bus2/<lat>/<lon>/', methods=['GET', 'POST'])
def get_near_bus2(lat, lon):
    return dbConn.get_near_bus2(lat, lon)

@app.route('/get_near_road/<lat>/<lon>/', methods=['GET', 'POST'])
def get_near_road(lat, lon):
    return dbConn.get_near_road(lat, lon)

@app.route('/get_all_pamiatky/', methods=['GET', 'POST'])
def get_all_pamiatky():
    return dbConn.get_all_pamiatky()

# @app.route('/get_pamiatky/', methods=['GET', 'POST'])
# def get_near_parks(lat, lon, dis):
#     return dbConn.get_near_parks()

if __name__ == '__main__':
    app.run(host='localhost', debug=True)
