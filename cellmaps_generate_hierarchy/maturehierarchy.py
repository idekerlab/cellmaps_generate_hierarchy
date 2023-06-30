import pandas as pd
import numpy as np
import math
import sys
import os
import argparse
import networkx as nx
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


### One step making ontology from the hidef Hierarchy
## make a long table of (parent, child, edgetype)

def create_ontology(path, minTermsize=4):
    '''
    path: the path to the hierarchy that need to make this format transformation

    '''
    ## read node table
    node_table = pd.read_csv(path + '.nodes', header=None, sep='\t')
    # print(node_table.head())
    # print(len(node_table))
    node_table.columns = ['terms', 'tsize', 'genes', 'stability']
    # node_table.genes = [g.split(' ') for g in node_table.genes] # change the genes column to list of genes
    # print(node_table.head())
    node_table_filtered = node_table[node_table['tsize'] >= minTermsize]
    # print(node_table[node_table['Num_genes']<minTermsize]['Node'])
    logger.info(str(len(node_table_filtered)))
    node_list = set(node_table_filtered['terms'])  ## get the list of nodes
    # print(node_list)

    new_rows = []
    for i, row in node_table_filtered.iterrows():
        for c in row['genes']:
            new_rows.append([row['terms'], c])  # for each gene, give the corresponding cluster number

    node_table_final = pd.DataFrame(new_rows, columns=['parent', 'child'])
    node_table_final['type'] = 'gene'

    ### Read edge table
    edge_table = pd.read_csv(path + '.edges', header=None, sep='\t')
    edge_table.columns = ['parent', 'child', 'type']
    # print(len(edge_table))
    # filtered so that only nodes bigger >=4 will be in here
    edge_table_filtered = edge_table[edge_table[['parent', 'child']].isin(list(node_list)).all(axis=1)]

    add_gene = []
    genecount = 0
    ## Find leaves and get their genes
    leaves = (set(edge_table_filtered['child'].unique())) - set(edge_table_filtered['parent'].unique())
    # print(leaves)
    for leaf in leaves:
        genes = get_genes(node_table_filtered, leaf)
        genecount += len(genes)
        # print(leaf, len(genes))
        for gene in genes:
            add_gene.append([leaf, gene, 'gene'])
    # print(len(add_gene))

    parent_to_child = edge_table_filtered.groupby('parent')['child'].apply(list)  # group the parents
    # print(parent_to_child)
    for parent, children in parent_to_child.iteritems():
        parent_genes = get_genes(node_table_filtered, parent)
        # print(parent_genes)
        child_genes = []
        for child in children:
            genes = get_genes(node_table_filtered, child)
            # print(f'length of child {child} is {len(genes)}')
            child_genes = set(child_genes).union(set(genes))
        # print(f'full length of child genes is {len(child_genes)}')
        only_parent = set(parent_genes) - set(child_genes)  ## genes only in parent did not pass to child
        genecount += len(only_parent)
        # print(parent, len(only_parent))
        if len(only_parent) >= 1:
            for gene in only_parent:
                add_gene.append([parent, gene, 'gene'])
    # print(len(add_gene))
    # print(genecount)
    add_rows = pd.DataFrame(add_gene, columns=['parent', 'child', 'type'])
    final_df = edge_table_filtered.append(add_rows)
    print(len(final_df))
    return final_df


# get the genes from the nodes file, split each gene by the space
def get_genes(nodes_df, term):
    genes = nodes_df.loc[nodes_df.terms == term]['genes']
    gene_list = []
    for g in genes:
        gene_list.extend(g.split(' '))
    return gene_list


## Load Edge Files and create ontology
def read_edge_table(path):
    edge_table = pd.read_csv(path, header=None, sep='\t')
    edge_table.columns = ['Parent', 'Child', 'EdgeType']
    return edge_table


## Load Node Files and make a long table of (parent, child, edgetype)
def read_node_table(path):
    node_table = pd.read_csv(path, header=None, sep='\t')
    # print(node_table.head())
    cd_list = []
    node_table.columns = ['Node', 'Num_genes', 'Genes', 'Persistence']
    for i, row in node_table.iterrows():
        cd = row['Genes']
        all_cds = cd.split(' ')
        cd_list.append(all_cds)
    ## each gene will be in one row
    node_table['Genes_list'] = cd_list

    new_rows = []
    for i, row in node_table.iterrows():
        for c in row['Genes_list']:
            new_rows.append([row['Node'], c])  # for each gene, give the corresponding cluster number

    node_table_final = pd.DataFrame(new_rows, columns=['Parent', 'Child'])
    node_table_final['EdgeType'] = 'gene'

    return node_table_final


## clean up the table, remove duplicated genes
def clean_table(df):
    only_nodes = df[df['EdgeType'] == 'default']
    only_genes = df[df['EdgeType'] == 'gene']

    ## for nodes
    node_to_gene = only_genes.groupby('Parent')['Child'].apply(list)  # each cluster, genes inside
    gene_to_node = only_genes.groupby('Child')['Parent'].apply(list)  # each gene, clusters they are present

    genes = list(only_genes['Child'].value_counts().keys())  # list of all genes
    print(len(genes))

    ## for edges
    parent_to_child = only_nodes.groupby('Parent')['Child'].apply(
        list)  # each cluster, the child cluster(s) they connected to
    child_to_parent = only_nodes.groupby('Child')['Parent'].apply(
        list)  # each cluster, the parent cluster(s) they connected to

    nodes = set(only_nodes['Parent'].value_counts().keys()).union(set(only_nodes[
                                                                          'Child'].value_counts().keys()))  # get the union between parent clusters and child clusters (all clusters without counting duplicates)
    nodes_priority = defaultdict(int)

    only_genes.loc[:, 'Priority'] = only_genes['Parent'].map(
        lambda x: get_depth(x, 0, child_to_parent))  # get the depth of each child

    keep_rows = []
    for g in genes:
        keep_rows.append(only_genes[only_genes['Child'] == g].sort_values(by='Priority', ascending=False).iloc[
                             0])  # sort genes based on depth (choose the top)

    kept_genes = pd.DataFrame(keep_rows)
    kept_genes = kept_genes[['Parent', 'Child', 'EdgeType']]
    final_df = only_nodes.append(kept_genes)

    return final_df


def get_depth(node, count, child_to_parent):
    if node in child_to_parent.keys():
        max_d = get_depth(child_to_parent[node][0], count + 1, child_to_parent)
        # save_n = child_to_parent[node][0]
        for n in child_to_parent[node]:
            d = get_depth(n, count + 1, child_to_parent)
            if d > max_d:
                max_d = d

        return max_d
    else:
        return count


def to_pandas_dataframe(G):
    e = G.edges(data=True)
    df = pd.DataFrame()
    df['source'] = [x[0] for x in e]
    df['target'] = [x[1] for x in e]
    df['type'] = [x[2]['type'] for x in e]
    return df


def get_termStats(G, hiergeneset):
    clusters = list(set(list(G.nodes())) - hiergeneset)
    tsize_list = []
    cgene_list = []
    descendent_list = []
    for c in clusters:
        infoset = nx.descendants(G, c)
        cgeneset = infoset.intersection(hiergeneset)
        tsize_list.append(len(cgeneset))
        cgene_list.append(list(cgeneset))
        descendent_list.append(list(infoset - cgeneset))
    df = pd.DataFrame(index=clusters)
    df['tsize'] = tsize_list
    df['genes'] = cgene_list
    df['descendent'] = descendent_list
    return df

def jaccard(A, B):
    if type(A) != set:
        A = set(A)
    if type(B) != set:
        B = set(B)
    return len(A.intersection(B)) / len(A.union(B))

def clean_shortcut(G):
    edge_df = to_pandas_dataframe(G)
    edge_df.columns = ['parent', 'child', 'type']
    for idx, row in edge_df.iterrows():
        if len(list(nx.all_simple_paths(G, row['parent'], row['child']))) > 1:
            G.remove_edge(row['parent'], row['child'])
            print('shortcut edges is removed between {} and {}'.format(row['parent'], row['child']))
    return

def reorganize(G, hiergeneset, ci_thre): # Add an edge if the nodes have containment index >=threshold
    iterate = True
    n_iter = 1
    while iterate:
        clear = True
        print('... starting iteration {}'.format(n_iter))
        ts_df = get_termStats(G, hiergeneset) # get the termStats from the networkx
        ts_df.sort_values('tsize', ascending=False, inplace=True)
        for comp, row in ts_df.iterrows():
            tmp = ts_df[ts_df['tsize'] < row['tsize']] # get all components smaller than this components
            if tmp.shape[0] == 0:
                continue
            comp_geneset = set(row['genes']) # get the set of genes
            descendent = row['descendent'] # get the list of descendent nodes
            for tmp_comp, tmp_row in tmp.iterrows():
                if tmp_comp in descendent: # skip if already in descendent
                    continue
                tmp_comp_geneset = set(tmp_row['genes'])
                # Check if satisfy ci_thre
                if len(comp_geneset.intersection(tmp_comp_geneset))/tmp_row['tsize'] >= ci_thre: #intersection of two components divided by the term size of the smaller component
                    # Check if child having higher weight than parent
                    # if cluster_weight[comp] < cluster_weight[tmp_comp]: ## do not have weight in hidef
                    print('{} is contained in {} with a CI bigger than threshold, add edge between'.format(tmp_comp, comp))
                    G.add_edge(comp, tmp_comp, type='default')
                    clear = False
                    descendent += tmp_row['descendent']
        # Further clean up using networkx to remove shortcut edges
        clean_shortcut(G)
        # Update variables
        n_iter += 1
        if clear:
            iterate = False
    if n_iter == 2:
        modified = False
    else:
        modified = True
    return modified

def merge_parent_child(G, hiergeneset, ji_thre):
    # Delete child term if highly similar with parent term
    # One parent-child relationship at a time to avoid complicacies involved in potential long tail
    print('... start removing highly similar parent-child relationship')
    similar = True
    merged = False
    while similar:
        clear = True
        edge_df = to_pandas_dataframe(G)
        ts_df = get_termStats(G, hiergeneset)
        default_edge = edge_df[edge_df['type'] == 'default'] # edges
        for idx, row in default_edge.iterrows():
            if jaccard(ts_df.loc[row['source']]['genes'], ts_df.loc[row['target']]['genes']) >= ji_thre:
                print('# Cluster pair {}->{} failed Jaccard, removing cluster {}'.format(row['source'], row['target'],
                                                                                         row['target']))
                clear = False
                merged = True
                parents = edge_df[edge_df['target'] == row['target']]['source'].values
                children = edge_df[edge_df['source'] == row['target']]['target'].values
                # Remove all parent->node edges
                for pnode in parents:
                    G.remove_edge(pnode, row['target'])
                for child_node in children:
                    etype = G[row['target']][child_node]['type']
                    # Remove all node->child edges
                    G.remove_edge(row['target'], child_node)
                    # Add all parent->child edges
                    for pnode in parents:
                        G.add_edge(pnode, child_node, type=etype)
                # Remove target node
                G.remove_node(row['target'])
                break
        if clear:
            similar = False
    # Clean up shortcuts introduced during node deleteing process
    clean_shortcut(G)
    return merged

def collapse_redundant(G, hiergeneset, min_diff):
    # Delete child term if highly similar with parent term
    # One parent-child relationship at a time to avoid complicacies involved in potential long tail
    print('... start removing highly redundant systems')
    while True:
        edge_df = to_pandas_dataframe(G)
        ts_df = get_termStats(G, hiergeneset)
        default_edge = edge_df[edge_df['type'] == 'default']
        to_collapse = []
        for idx, row in default_edge.iterrows():
            parentSys, childSys, _ = row.values
            if ts_df.loc[parentSys]['tsize'] - ts_df.loc[childSys]['tsize'] < min_diff:
                to_collapse.append([parentSys, childSys])
        if len(to_collapse) == 0:
            print('nothing to collapse')
            return
        to_collapse = pd.DataFrame(to_collapse, columns=['parent', 'child'])
        # print(to_collapse)
        # cidx = to_collapse['weight'].idxmin()
        deleteSys = to_collapse.loc['child']
        print('# Cluster pair {}->{} highly redundant, removing cluster {}'.format(to_collapse.loc['parent'],
                                                                                   to_collapse.loc['child'],
                                                                                   deleteSys))
        parents = edge_df[edge_df['target'] == deleteSys]['source'].values
        children = edge_df[edge_df['source'] == deleteSys]['target'].values
        # Remove all parent->node edges
        for pnode in parents:
            G.remove_edge(pnode, deleteSys)
        for child_node in children:
            etype = G[deleteSys][child_node]['type']
            # Remove all node->child edges
            G.remove_edge(deleteSys, child_node)
            # Add all parent->child edges
            for pnode in parents:
                G.add_edge(pnode, child_node, type=etype)
        # Remove target node
        G.remove_node(deleteSys)

parser = argparse.ArgumentParser()
parser.add_argument('--outprefix', help='output_dir/file_prefix for the output file')
parser.add_argument('--ci_thre', type=float, default=0.75, help='Containment index threshold')
parser.add_argument('--ji_thre', type=float, default=0.9,
                    help='Jaccard index threshold for merging similar clusters')
parser.add_argument('--minSystemSize', type=int, default=4,
                    help='Minimum number of proteins requiring each system to have.')
parser.add_argument('--path_to_alignOntology', help='Full path to alignOntology.')
parser.add_argument('--min_diff', type=int, default=1, help='Minimum difference in number of proteins for every parent-child pair.')
args = parser.parse_args()

outprefix = args.outprefix
minSystemSize = args.minSystemSize

ci_thre = args.ci_thre
ji_thre = args.ji_thre
print('Containment index threshold: {}'.format(ci_thre))
print('Jaccard index threshold: {}'.format(ji_thre))

f = outprefix
ont = create_ontology(outprefix, minSystemSize)
hiergeneset = set(ont[ont['type'] == 'gene']['child'].values)

G = nx.from_pandas_edgelist(ont, source='parent', target='child', edge_attr='type', create_using=nx.DiGraph())

if not nx.is_directed_acyclic_graph(G):
    raise ValueError('Input hierarchy is not DAG!')

while True:
    modified = reorganize(G, hiergeneset, ci_thre)
    merged = merge_parent_child(G, hiergeneset, ji_thre)
    if not modified and not merged:
        break

collapse_redundant(G, hiergeneset, args.min_diff)
# Output as ddot edge file
clean_shortcut(G)
edge_df = to_pandas_dataframe(G)
edge_df.to_csv('{}.pruned.ont'.format(outprefix), header=False, index=False, sep='\t')
run_termStats = '{}/ontologyTermStats {} genes > {}'.format(args.path_to_alignOntology,
                                                  '{}.pruned.ont'.format(outprefix),
                                                  '{}.pruned.nodes'.format(outprefix))
os.system(run_termStats)


## step to clean the termStats file and make it the same format as hidef output
nodes = pd.read_csv(outprefix+'.pruned.nodes', sep = '\t', header = None)
nodes.columns = ['terms', 'Size', 'MemberList']
original_nodes = pd.read_csv(outprefix + '.nodes', sep = '\t', header = None)
nodes['Stability'] = original_nodes.loc[nodes.index.values, 3]
nodes = nodes.set_index('terms')
cleaned= []
for i, rows in nodes.iterrows():
    genes = [g for g in rows['MemberList'].split(',') if len(g) > 1]
    cleaned.append(' '.join(genes))
nodes['MemberList'] = cleaned
#nodes['LogSize'] = [math.log2(x) for x in nodes['Size']] ## add logsize to the nodes file (to read in cytoscape)
nodes.sort_values(by='Size', ascending=False, inplace=True)
nodes.to_csv(outprefix+'.pruned.nodes', header=False, sep='\t')

#edges = edge_df[edge_df['type']=='default']# create the hidef format edges
edges = edge_df.loc[edge_df['type'] == 'default', :]
edges.to_csv(outprefix+'.pruned.edges',sep = '\t', header=None,index=None)
G = nx.from_pandas_edgelist(edges, source='source', target='target', create_using=nx.DiGraph())
for c in nodes.columns:
    dic = nodes[c].to_dict()
    nx.set_node_attributes(G, dic, c)
nx.write_gml(G, outprefix+'.pruned.gml')

print(f'Number of edges is {len(edges)}, number of nodes are {len(nodes)}')
print('=== finished mature_hier_structure.py ====')