(define (concat x y) (match x
    [(Cons x xs) (cons x (concat xs y))]
    [(Null) y]
))