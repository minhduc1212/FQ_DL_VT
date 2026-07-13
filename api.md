# API
## Tìm kiếm
```
method: GET
url: http://localhost:9999/search?query=từ khóa&page=số trang
```
## Lấy thông tin chi tiết truyện
```
method: GET
url: http://localhost:9999/info?book_id=ID truyện
```
### Lấy danh sách chương (Mục lục)

```
method: GET
url: http://localhost:9999/catalog?book_id=ID truyện
```
### Lấy nội dung chương
```
method: GET
url: http://localhost:9999/content?item_id=itemId của chương
```
# Lấy truyện trong mục Khám phá
```
method: GET
url: http://localhost:9999/reading/bookapi/bookmall/cell/change/v1/
params: Giống hệt với tham số của ứng dụng gốc

method: GET
url: http://localhost:9999/reading/bookapi/new_category/landing/v/
params: Giống hệt với tham số của ứng dụng gốc
```

