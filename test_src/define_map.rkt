(define (map f l) (match l
[(Cons x xs) (cons (f x) (map f xs))]
[(Nil) null]))