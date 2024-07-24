let error = true

let res = [
  db.dogs.drop(),
  db.dogs.createIndex({ dog_name: 1 }, { unique: true }),
  db.dogs.createIndex({ admin: 1 }),
  db.dogs.insert({ dog_name: 'Doggo 1', admin: false }),
  db.dogs.insert({ dog_name: 'Doggo 2 (Superdog)', admin: true }),
]

printjson(res)

if (error) {
  print('Error, exiting')
  quit(1)
}
