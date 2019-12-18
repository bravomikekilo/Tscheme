(define (take-while f l) (match l
    [(Cons x xs) (if (f x) (cons x (take-while f xs)) null)]
    [(Null) null]
))