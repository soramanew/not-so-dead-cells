from main import main

if __name__ == "__main__":
    from cProfile import Profile
    from pstats import Stats

    pr = Profile()
    pr.enable()

    main()

    pr.disable()
    stats = Stats(pr)
    print()
    stats.sort_stats("cumulative").print_stats(30)
