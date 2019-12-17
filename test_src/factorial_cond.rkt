(define (factorial x)
  (cond
     ((= x 0) 1)
     (#t (* x
            (factorial (- x 1)))
     )))