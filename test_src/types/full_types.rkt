(define-sum (Tree a)
    [Branch a (Tree a) (Tree a)]
    [Leaf a])

(define-sum (List a)
    [Cons a (List a)]
    [Nil])

(define-sum (Maybe a)
    [Just a]
    [Nothing])

(define-sum Shape
    [Rect Number Number]
    [Circle Number])

(define-record Point
    [x Number]
    [y Number])

(define-record (Pair a)
    [first a]
    [second b])
