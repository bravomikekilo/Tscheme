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

(define-sum Shape
    [Rect Number Number]
    [Circle Number])
