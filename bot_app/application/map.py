import folium, json, os
from folium import plugins
from folium import FeatureGroup
from folium.plugins import MarkerCluster

class Map:
    def __init__(self) -> None:

        with open(r"JSONs\ua-cities.json", encoding="utf-8") as f:
            d = json.load(f)

        self.city_list = []
        self.city_lon = []
        self.city_lat = []

        for region in d[0]['regions']:
            for item in region['cities']:
                self.city_list.append(item['name'].lower())
                self.city_lon.append(item['lat'].lower())
                self.city_lat.append(item['lng'].lower())

        with open(r"JSONs\ua-cities-ua.json", encoding="utf-8") as f:
            d_ua = json.load(f)

        self.city_list_ua = []
        self.city_lon_ua = []
        self.city_lat_ua = []

        for region in d_ua[0]['regions']:
            for item in region['cities']:
                self.city_list_ua.append(item['name'].lower())
                self.city_lon_ua.append(item['lat'].lower())
                self.city_lat_ua.append(item['lng'].lower())

        self.map = folium.Map(width=1520,
                            height=720,
                            location=[49.05, 30.60],
                            tiles='openstreetmap',
                            zoom_start=6,
                            min_zoom=1,
                            max_zoom=14)

        plugins.Geocoder().add_to(self.map)

        fmtr = "function(num) {return L.Util.formatNum(num, 3) + ' º ';};"
        plugins.MousePosition(
            position="topright",
            separator=" | ",
            prefix="Coordinates:",
            lat_formatter=fmtr,
            lng_formatter=fmtr).add_to(self.map)

        minimap = plugins.MiniMap()
        self.map.add_child(minimap)

        plugins.Fullscreen().add_to(self.map)

        # plugins.LocateControl().add_to(map)

        plugins.MeasureControl(position='topright',
                               primary_length_unit='meters',
                               secondary_length_unit='miles',
                               primary_area_unit='sqmeters',
                               secondary_area_unit='acres').add_to(self.map)

        folium.TileLayer('Stamen Toner').add_to(self.map)
        folium.TileLayer('Stamen Terrain').add_to(self.map)
        folium.TileLayer('Stamen Watercolor').add_to(self.map)
        folium.TileLayer('openstreetmap').add_to(self.map)
        folium.TileLayer('cartodbpositron').add_to(self.map)
        folium.TileLayer('cartodbdark_matter').add_to(self.map)

        folium.TileLayer(
            tiles='https://tiles.openrailwaymap.org/standard/{z}/{x}/{y}.png',
            attr='OpenRailwayMap',
            name='OpenRailwayMap'
        ).add_to(self.map)

        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Satellite',
            overlay=False,
            control=True
        ).add_to(self.map)

        plugins.Draw().add_to(self.map)

    def map_creation(self, channels, filtered_cities_dict, username, region):
            
            if channels == 'ru':
                city_list = self.city_list
            if channels == 'ua':
                city_list = self.city_list_ua

            marker_cluster = MarkerCluster(name='Clusters').add_to(self.map)
            marker_points = FeatureGroup(name='All markers', show=False).add_to(self.map)

            for i in range(0, len(filtered_cities_dict)):

                if len(filtered_cities_dict[city_list[i]]) != 0:

                    folium.Marker(location=[self.city_lon[i], self.city_lat[i]],
                                popup=filtered_cities_dict[city_list[i]],
                                tooltip=[city_list[i].capitalize(), len(filtered_cities_dict[city_list[i]]), 'новость(и)'],
                                icon=folium.Icon(color='orange' if (len(filtered_cities_dict[city_list[i]])) > 4 else 'green',
                                                icon="info-sign")).add_to(marker_cluster)

                    folium.Marker(location=[self.city_lon[i], self.city_lat[i]],
                                popup=filtered_cities_dict[city_list[i]],
                                tooltip=[city_list[i].capitalize(), len(filtered_cities_dict[city_list[i]]), 'новость(и)'],
                                icon=folium.Icon(color='orange' if (len(filtered_cities_dict[city_list[i]])) > 4 else 'green',
                                                icon="info-sign")).add_to(marker_points)
            folium.LayerControl().add_to(self.map)

            if not os.path.isdir(f'output\{username}'):
                os.mkdir(f'output\{username}')

            if region:
                map_name = f'output\{username}\\region_map_{username}.html'
            else:
                map_name = f'output\{username}\map_{username}.html'

            self.map.save(map_name)

    def tag_map_creation(self, channels, filtered_tag_dict, tag_words, username):

        if channels == 'ru':
            city_list = self.city_list
        if channels == 'ua':
            city_list = self.city_list_ua

        for i in range(len(filtered_tag_dict)):

            if len(filtered_tag_dict[city_list[i]]) != 0:

                folium.Marker(location=[self.city_lon[i], self.city_lat[i]],
                              popup=filtered_tag_dict[city_list[i]],
                              tooltip=[city_list[i].capitalize(), len(filtered_tag_dict[city_list[i]]), str(tag_words[-1])],
                              icon=folium.Icon(color='blue', icon="info-sign")).add_to(self.map)
        folium.LayerControl().add_to(self.map)

        
        if not os.path.isdir(f'output\{username}'):
            os.mkdir(f'output\{username}')

        tag_map_name = f'output\{username}\\tag_map_{username}.html'
        self.map.save(tag_map_name)