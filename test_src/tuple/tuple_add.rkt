(define (tuple-add x) (match x
    [(tuple t1 t2) (+ t1 t2)]
))

(print (tuple-add (tuple 1 2)))