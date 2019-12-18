(define (drop i l) (if (= i 0) l (match l
    [(Cons _ xs) (drop (- i 1) xs)]
    [(Null) null])))
