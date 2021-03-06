import snap
import numpy as np
import networkx as nx
import community
import matplotlib.pyplot as plt
import community_layout
import collections
import csv

G_nx = None
node_list = []
investor_list = []
node_size_list = []
weights_dict = {}
transactions_startup2vc = {}

def rescale(investor_size_list, new_min = 50, new_max = 800):
    old_max = max(investor_size_list)
    old_min = min(investor_size_list)
    return [int(1.0*(new_max - new_min) * (x - old_min) / (old_max - old_min) + new_min) for x in investor_size_list]

def construct_graph(network, graph, is_weighted = False, weight_method = "default"):
    if network == "investor":
        node_list_file = "data/investor_list.txt"
        edge_list_file = graph
        if weight_method == "default":
            edge_weights_file = "data/investor_network_undirected_weights.txt"
        elif weight_method == "jaccard":
            edge_weights_file = "data/investor_network_undirected_weights_jaccard.txt"
    elif network == "startup":
        node_list_file = "data/startup_list.txt"
        edge_list_file = graph
        edge_weights_file = "data/startup_network_undirected_weights.txt"

    f = open(node_list_file, "r")
    for line in f:
        name, w = line.strip().rsplit(' ', 1)
        node_list.append(name)
        node_size_list.append(int(w))

    if network == "startup":
        f = open("data/investor_list.txt", "r")
        for line in f:
            name, w = line.strip().rsplit(' ', 1)
            investor_list.append(name)

        f = open("data/transactions.csv", "r")
        csv_reader = csv.reader(f, delimiter=",", quotechar='"')
        for vc, startup, round, time in csv_reader:
            transactions_startup2vc[startup] = vc

    if is_weighted and edge_weights_file is not None:
        f = open(edge_weights_file, "r")
        for line in f:
            s, d, w = line.strip().split()
            s = int(s)
            d = int(d)
            weights_dict[(s, d)] = float(w)

    G = nx.Graph()
    if edge_list_file.endswith("txt"):
        f = open(edge_list_file, "r")
        f.readline()
        f.readline()
        f.readline()
        for line in f:
            s, d = [int(i) for i in line.strip().split()]
            G.add_node(s, name=node_list[s])
            G.add_node(d, name=node_list[d])
            if is_weighted:
                G.add_edge(s, d, weight=weights_dict[(s, d)])
            else:
                G.add_edge(s, d)
    elif edge_list_file.endswith("graph"):
        FIn = snap.TFIn(edge_list_file)
        G_snap = snap.TUNGraph.Load(FIn)
        for edge in G_snap.Edges():
            s, d = edge.GetSrcNId(), edge.GetDstNId()
            G.add_node(s, name=node_list[s])
            G.add_node(d, name=node_list[d])
            if is_weighted:
                G.add_edge(s, d, weight=weights_dict[(s, d)])
            else:
                G.add_edge(s, d)

    print("%s %s" % ("weighted" if is_weighted else "unweighted", weight_method))
    print("nodes", G.number_of_nodes(), "edges", G.number_of_edges())

    # configuration graph
    # deg_seq = [d for n,d in G.degree()]
    # G_conf = nx.configuration_model(deg_seq)
    # G = G_conf
    # print("config model nodes", G_conf.number_of_nodes(), "edges", G_conf.number_of_edges())
    return G

# def get_vc_for_startup_community(startup_communities):
#     f = open("data/transactions.csv", "r")
#     csv_reader = csv.reader(f, delimiter=",", quotechar='"')
#     transactions = {}
#     for vc, startup, round, time in csv_reader:
#         transactions[startup] = vc
#
#     vc_comm = {}
#     for com, startups in startup_communities.items():
#         vc_comm[com] =
#     return vc_comm

def louvain_partition_plot(network, graph, is_weighted = False, weight_method = "default", randomize=None):

    G_nx = construct_graph(network, graph, is_weighted, weight_method)

    ## degree distribution

    degree_sequence = sorted([d for n, d in G_nx.degree()], reverse=True)
    degreeCount = collections.Counter(degree_sequence)
    print("max degree", max(degreeCount))
    deg, cnt = zip(*degreeCount.items())
    plt.plot(deg, cnt)
    plt.xlabel("Node degree")
    plt.ylabel("Count")
    plt.title("Degree distribution")
    plt.show()

    ## Louvain partitioning

    partition = community.best_partition(G_nx, randomize=randomize)

    size = float(len(set(partition.values())))
    print("# community", size)
    print("modularity", community.modularity(partition, G_nx))
    # return size, community.modularity(partition, G_nx)

    ## print communities

    count = 0.
    communities = {}
    comm_size_list = []

    for com in set(partition.values()):
        # count += 1.
        list_nodes = [n for n in partition.keys() if partition[n] == com]
        communities[com] = list_nodes
        comm_size_list.append(len(list_nodes))
        print("#######community %i size %i" % (com, len(list_nodes)))

        if network == "startup":
            print("VCs who invest in this community:")
            for n in set([transactions_startup2vc[node_list[startup]] for startup in list_nodes]):
                print(n)
            print("\nStartups:")
        for n in list_nodes:
            print("%i %s" % (n, node_list[n]))
    print("Communities", communities)

    # write communities to txt
    # with open("data/investor_network_undirected_w_louvain_cc.txt", 'w') as f:
    #     for com in set(partition.values()):
    #         list_nodes = [n for n in partition.keys() if partition[n] == com]
    #         communities[com] = list_nodes
    #         comm_size_list.append(len(list_nodes))
    #         f.write("#######community %i size %i\n" % (com, len(list_nodes)))
    #
    #         for n in list_nodes:
    #             f.write("%i : %s : %i\n" % (n, node_list[n], G_nx.degree(n)))

    # degree
    # for com in set(partition.values()):
    #     G_sub = G_nx.subgraph(communities[com])
    #     deg_in = 2*G_sub.number_of_edges()
    #     deg_total = 0
    #     for _,deg in G_nx.degree(communities[com]):
    #         deg_total += deg
    #     deg_out = deg_total - deg_in
    #     print
    #     # print(G_nx.degree(communities[com]))
    #     print("G_sub.number_of_edges", G_sub.number_of_edges())
    #     print("G_sub.degree in", deg_in)
    #     print("G_sub.degree total", deg_total)
    #     print("G_nx.degree out", deg_out)


    print("Community size", sorted(comm_size_list, reverse=True))
    plt.plot(np.arange(size), sorted(comm_size_list, reverse=True))
    plt.yscale("log")
    plt.xlabel("Community")
    plt.ylabel("Number of nodes in community")
    plt.title("Community size distribution")
    plt.show()

    ## plot

    # plot degree of nodes in communities
    deg_list = []
    for com in set(partition.values()):
        nodes = [n for n in partition.keys() if partition[n] == com]
        deg_list.extend(sorted(G_nx.degree(nodes), key=lambda x: x[1], reverse=True))
    plt.plot(map(lambda x: x[1], deg_list))
    plt.yscale("log")
    plt.xlabel("Nodes sorted by communities")
    plt.ylabel("Node degree")
    plt.title("Node degree by communities")
    plt.show()

    # draw graph
    # pos = nx.spring_layout(G_nx)
    pos = community_layout.community_layout(G_nx, partition)
    # pos = community_layout._position_communities(G_nx, partition)

    # nx.draw_networkx_nodes(G_nx, pos, list_nodes, node_size = 10, cmap=plt.cm.RdYlBu, node_color = np.array(partition.values())) #str(count / size)
    nx.draw_networkx_nodes(G_nx, pos, node_size=rescale(node_size_list), node_color=list(partition.values()))
    nx.draw_networkx_edges(G_nx, pos, alpha=0.1)
    # nx.draw_spring(G_nx, cmap = plt.get_cmap('jet'), node_color = partition.values(), node_size=50, with_labels=False)
    # nx.draw(G_nx, pos, node_size=100, node_color=partition.values())
    plt.show()


# plot dynamic
def draw(data1,data2):
    t1 = np.arange(2009,2019,1)
    t2 = np.arange(2009,2019,1)

    fig, ax1 = plt.subplots()

    color = 'tab:red'
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Number of Communities', color=color)
    ax1.plot(t1, data1, marker = "*", color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    # disk1 = plt.Circle((t1[2], data1[2]), 0.3, color='k', fill=False)
    # ax1.add_artist(disk1)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('Modularity', color=color)  # we already handled the x-label with ax1
    ax2.plot(t2, data2, marker = "*",color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    # disk2 = plt.Circle((t2[2], data2[2]), 0.3, color='k', fill=False)
    # ax2.add_artist(disk2)

    # fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.title("Number of Communities and Modularities vs. Year")
    plt.savefig('num_communities_and_modularities_vs_year.png')
    fig_size= 7,7
    plt.rcParams["figure.figsize"] = fig_size
    print plt.rcParams["figure.figsize"]
    plt.show()


def main():
    louvain_partition_plot("investor", graph="data/investor_network_undirected_unweighted.txt",
                           is_weighted=False, weight_method="jaccard", randomize=None)
    # louvain_partition_plot("investor", graph="data/Giu_unweighted_by_year/Giu_2018.graph",
    #                        is_weighted=False, weight_method="default", randomize=False)
    # louvain_partition_plot("startup", is_weighted=False)
    # louvain_partition_plot("startup", graph="data/startup_network_undirected_unweighted.txt",
    #                        is_weighted=False, weight_method="default", randomize=None)

if __name__ == '__main__':
	main()

    # sizes = [9, 10, 7, 9, 10, 12, 11, 16, 15, 18]
    # sizes = []
    # modularities = []
    # for year in range(2009, 2019):
    #     name = "data/Giu_unweighted_by_year/Giu_%i.graph" % year
    #     print(name)
    #     # reset graph
    #     G_nx = nx.Graph()
    #     node_list = []
    #     investor_list = []
    #     node_size_list = []
    #     weights_dict = {}
    #     transactions_startup2vc = {}
    #     size, modularity = louvain_partition_plot("investor", graph=name,
    #                            is_weighted=False, weight_method="default", randomize=False)
    #     sizes.append(size)
    #     modularities.append(modularity)
    #
    # draw(sizes, modularities)


# unweighted
# (512, 3232)
# ('# community', 82.0)
# ('modularity', 0.23759403757903635)
# (439, 3232)
# ('# community', 9.0)
# ('modularity', 0.24210406953056077)

# weighted
# (439, 3232)
# ('# community', 9.0)
# ('modularity', 0.20910374606407073)


# G_snap = snap.LoadEdgeList(snap.PUNGraph, "data/investor_network_undirected_unweighted.txt", 0, 1)
# for n in G_snap.Nodes():
#     n.g


# G = nx.Graph()
# f = open("data/investor_list.txt", "r")
# i = 0
# for line in f:
#     G_nx.add_node(i, name=line)
#     i += 1
#
# print("# nodes", G.GetNodes(), "# edges", G.GetEdges())
#
# CmtyV = snap.TCnComV()
# modularity = snap.CommunityCNM(G, CmtyV)
# print("CommunityCNM modularity", modularity, "# community", CmtyV.Len())
#
# CmtyV = snap.TCnComV()
# modularity = snap.CommunityGirvanNewman(G, CmtyV)
# print("CommunityGirvanNewman modularity", modularity, "# community", CmtyV.Len())

# ('# nodes', 439, '# edges', 3232)
# ('CommunityCNM modularity', 0.22546502793843695, '# community', 9)
# ('CommunityGirvanNewman modularity', 0.02526693920939125, '# community', 302)

# sizes = [434, 395, 344, 340, 323, 319, 306, 301, 300, 270, 251, 236, 173, 162, 158, 119, 118, 87, 17, 16, 15, 15, 12, 11, 7, 7, 6, 6, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
# plt.plot(sizes)
# plt.xlabel("Community")
# plt.ylabel("Number of nodes in community")
# plt.title("Community size distribution")
# plt.show()