(define (take i l) (match l
    [(Cons x xs) (if (= i 0) null (cons x (take (- i 1) xs)))]
    [(Nil) null]
))