

Create varibales for the population
Generate random 10 populations 
calculate the fitness of each population 
Selection
    Tournament selection 
        selecting random 3 and then two best among those 3
    Roulette selection 
        each parent has chance of selection base on fitness value
    Stochastic Universal Sampling
        instead of selecting from n spins it uses one spin to create evenly spaced pointer s and each individual gets drawn based on number of pointers it on its linear distribution
    rank based selection
        each parent is given rank based on fitness
        expected(r) = (2 − s) + 2(s − 1) · (r − 1) / (N − 1)
        where is s is selection pressure between 1-2
        then expected copies can be selected based on roulette or sus
    Boltzmann selection
        weight_i = exp(f_i / T)
        t higher means exploration any parents can be selected
        t lower is always close to best selected

Replacement
    Generational 
        replacing everyone
        or replacing everyone keeping best two (elitism)
    steaty-state
        replace worst or oldest single or two parents
    (μ, λ) and (μ+λ)
        creating λ child which share same pool and best from parent and child.
    
    Diversity-preserving replacement
        Restricted tournament replacement
            only replacing most similar parent if child is better
            similar is by behaviour distance 
    