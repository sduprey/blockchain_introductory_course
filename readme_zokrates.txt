password = "password"
as a bytes array
[112, 97, 115, 115, 119, 111, 114, 100]
its hash
5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8
as bytes
[
  94, 136, 72, 152, 218, 40, 4, 113,
  81, 208, 229, 111, 141, 198, 41, 39,
  115, 96, 61, 13, 106, 171, 189, 214,
  42, 17, 239, 114, 29, 21, 66, 216
]

zokrates compile -i password_hash.zok
zokrates setup
zokrates compute-witness -a \
112 97 115 115 119 111 114 100 \
94 136 72 152 218 40 4 113 \
81 208 229 111 141 198 41 39 \
115 96 61 13 106 171 189 214 \
42 17 239 114 29 21 66 216

zokrates generate-proof

zokrates verify