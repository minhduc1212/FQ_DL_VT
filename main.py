import requests

url = "http://localhost:9999/search?query=朕为夏君&page=1"
response = requests.get(url)
print(response.json()) # Tìm ID truyện ở trong này

url_id = "http://localhost:9999/catalog?book_id=7484611801053678654"
resp = requests.get(url_id)
print(resp.json())