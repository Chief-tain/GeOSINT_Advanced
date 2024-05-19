from io import BytesIO

import folium, json, os
from folium import plugins
from folium import FeatureGroup
from folium.plugins import MarkerCluster

class MapCreation:
    def __init__(
        self,
        width: int = 1300,
        height: int = 800,
        location: list[float] = [49.05, 30.60],
        marker: bool = False
        ) -> None:

        with open("coords/ua-cities.json", encoding="utf-8") as f:
            d = json.load(f)

        self.city_list = []
        self.city_lon = []
        self.city_lat = []

        for region in d[0]['regions']:
            for item in region['cities']:
                self.city_list.append(item['name'].lower())
                self.city_lon.append(item['lat'].lower())
                self.city_lat.append(item['lng'].lower())

        self.map = folium.Map(
            width=width,
            height=height,
            location=location,
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

        # folium.TileLayer('Stamen Toner').add_to(self.map)
        # folium.TileLayer('Stamen Terrain').add_to(self.map)
        # folium.TileLayer('Stamen Watercolor').add_to(self.map)
        # folium.TileLayer('cartodbpositron').add_to(self.map)
        # folium.TileLayer('cartodbdark_matter').add_to(self.map)
        folium.TileLayer('openstreetmap').add_to(self.map)

        # folium.TileLayer(
        #     tiles='https://tiles.openrailwaymap.org/standard/{z}/{x}/{y}.png',
        #     attr='OpenRailwayMap',
        #     name='OpenRailwayMap'
        # ).add_to(self.map)

        # folium.TileLayer(
        #     tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        #     attr='Esri',
        #     name='Esri Satellite',
        #     overlay=False,
        #     control=True
        # ).add_to(self.map)

        plugins.Draw().add_to(self.map)
        
        if marker:
            marker_points = FeatureGroup(name='All markers').add_to(self.map)
            folium.Marker(location=location, icon=folium.Icon(icon="info-sign")).add_to(marker_points)
            

    def map_creation(
        self,
        filtered_cities_dict: dict
        ):
            
            city_list = self.city_list
            total_points = 0

            marker_cluster = MarkerCluster(name='Clusters').add_to(self.map)
            marker_points = FeatureGroup(name='All markers', show=False).add_to(self.map)

            for i in range(0, len(filtered_cities_dict)):

                if len(filtered_cities_dict[city_list[i]]) != 0:

                    folium.Marker(
                        location=[self.city_lon[i], self.city_lat[i]],
                        popup=filtered_cities_dict[city_list[i]],
                        tooltip=[city_list[i].capitalize(), len(filtered_cities_dict[city_list[i]]), 'новость(и)'],
                        icon=folium.Icon(color='orange' if (len(filtered_cities_dict[city_list[i]])) > 4 else 'green',
                                        icon="info-sign")
                        ).add_to(marker_cluster)

                    folium.Marker(
                        location=[self.city_lon[i], self.city_lat[i]],
                        popup=filtered_cities_dict[city_list[i]],
                        tooltip=[city_list[i].capitalize(), len(filtered_cities_dict[city_list[i]]), 'новость(и)'],
                        icon=folium.Icon(color='orange' if (len(filtered_cities_dict[city_list[i]])) > 4 else 'green',
                                        icon="info-sign")
                        ).add_to(marker_points)
                    
                    total_points += 1
                    
            folium.LayerControl().add_to(self.map)
            
            buffer = BytesIO()
            self.map.save(buffer, close_file=False)
            
            return buffer, total_points

    def tag_map_creation(self, filtered_tag_dict, tag_words):
        
        city_list = self.city_list
        total_points = 0

        for i in range(len(filtered_tag_dict)):
            if len(filtered_tag_dict[city_list[i]]) != 0:
                folium.Marker(
                    location=[self.city_lon[i], self.city_lat[i]],
                    popup=filtered_tag_dict[city_list[i]],
                    tooltip=[city_list[i].capitalize(), len(filtered_tag_dict[city_list[i]]), str(tag_words[-1])],
                    icon=folium.Icon(color='blue', icon="info-sign")
                    ).add_to(self.map)
                
                total_points += 1
                
        folium.LayerControl().add_to(self.map)
        
        buffer = BytesIO()
        self.map.save(buffer, close_file=False)
        
        return buffer, total_points, tag_words

