(define (drop-while f l) (match l
    [(Cons x xs) (if (f x) (drop-while f xs) (cons x xs))]
    [(Null) null]
))