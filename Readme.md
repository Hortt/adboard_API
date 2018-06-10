## Input examples:
### All Boards
```
curl --request GET \
  --url http://127.0.0.1:5000/ \
  --header 'Authorization: 1Dennis:sxsxsx123' \
  --header 'Content-Type: application/javascript'
```
### Single Board
```
curl --request GET \
  --url http://127.0.0.1:5000/1 \
  --header 'Authorization: 1Dennis:sxsxsx123' \
  --header 'Content-Type: application/json'
```
### Insert new Board
```
curl --request POST \
  --url http://127.0.0.1:5000/ \
  --header 'Authorization: 1Dennis:sxsxsx123' \
  --header 'Content-Type: application/json' \
  --data '{
        "author": "1Dessss2nnis",
        "name": "Lets listen222sw23 s2om22222212e music"
    }'
```
### Like a board
```
curl --request PUT \
  --url http://127.0.0.1:5000/3322/like \
  --header 'Authorization: 1Dennis:sxsxsx123' \
  --header 'Content-Type: application/javascript' \
  --data '{"author": "3Dennis", "comment": "sxqsxsx123confirm_password sxsxsx123"}'
```
### Insert a comment
```
curl --request POST \
  --url http://127.0.0.1:5000/1/insert_comment \
  --header 'Authorization: denn1111is111:sxsxsx' \
  --header 'Content-Type: application/javascript' \
  --data '{"author": "denn1111is111", "comment": "sxsxsxc4wr3r3fff34erfdonfirmsxsxsx"}'
```
### Create new user
```
curl --request POST \
  --url http://127.0.0.1:5000/sign_up \
  --header 'Content-Type: application/javascript' \
  --data '{"name": "denn1111is111", "password": "sxsxsx", "confirm":"sxsxsx"}'
```

https://documenter.getpostman.com/view/3753127/RWEcNzs4
