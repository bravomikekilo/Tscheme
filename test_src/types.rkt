(define-sum (Tree a)
    [Branch a (Tree a) (Tree a)]
    [Leaf a])

(define-sum (Maybe a)
    [Just a]
    [Nothing])

(define-sum Shape
    [Rect Number Number]
    [Circle Number])

