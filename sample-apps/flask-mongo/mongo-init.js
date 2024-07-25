let error = true

let res = [
  db.dogs.drop(),
  db.dogs.createIndex({ dog_name: 1 }, { unique: true }),
  db.dogs.createIndex({ pswd: 1 }),
  db.dogs.insert({ dog_name: 'Doggo 1', pswd: "xyz" }),
  db.dogs.insert({ dog_name: 'Doggo 2 (Superdog)', pswd: "admin_pass" }),
]

printjson(res)

if (error) {
  print('Error, exiting')
  quit(1)
}
