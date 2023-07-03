import pandas as pd

import os
import networkx as nx
import logging

logger = logging.getLogger(__name__)


class HiDeFHierarchyRefiner(object):
    """
    Refines HiDeF hierarchy output by removing highly similar terms.
    This code derived from maturehierarchy.py developed by (## todo Leah who created this?)

    """

    TERMS_COL = 'terms'
    TSIZE_COL = 'tsize'
    GENES_COL = 'genes'
    STABILITY_COL = 'stability'

    TYPE_COL = 'type'
    PARENT_COL = 'parent'
    CHILD_COL = 'child'

    GENE_TYPE = 'gene'
    DEFAULT_TYPE = 'default'

    NODES_SUFFIX = '.nodes'
    EDGES_SUFFIX = '.edges'

    def __init__(self,
                 ci_thre=0.75,
                 ji_thre=0.9,
                 min_term_size=4,
                 min_diff=1):
        """
        Constructor

        :param ci_thre: Containment index threshold
        :param ji_thre: Jaccard index threshold for merging similar clusters
        :param min_system_size: Minimum number of proteins requiring each system to have
        :param min_diff: Minimum difference in number of proteins for every parent-child pair
        """
        self._ci_thre = ci_thre
        self._ji_thre = ji_thre
        self._min_term_size = min_term_size
        self._min_diff = min_diff

    @staticmethod
    def _get_node_table_from_hidef(nodes_file):
        """
        Takes a HiDeF nodes file and creates
        a :py:class:`pandas.DataFrame`

        **Example HiDeF edges file:**

        .. code-block::

            Cluster1-408    4       1528 2310 2666 4273     10
            Cluster1-409    4       126 3366 3794 446       10
            Cluster1-410    4       1522 2733 4334 4542     10

        **Resulting DataFrame:**

        .. code-block::

            terms           tsize   genes                   stability
            Cluster1-408    4       1528 2310 2666 4273     10
            Cluster1-409    4       126 3366 3794 446       10
            Cluster1-410    4       1522 2733 4334 4542     10

        :param nodes_file:
        :type nodes_file: str
        :return: DataFrame of the HiDeF nodes file
        :rtype: :py:class:`pandas.DataFrame`
        """
        node_table = pd.read_csv(nodes_file, header=None, sep='\t')
        logger.debug('nodes table head: ' + str(node_table.head()))
        logger.debug('Size of node table: ' + str(len(node_table)))

        node_table.columns = [HiDeFHierarchyRefiner.TERMS_COL,
                              HiDeFHierarchyRefiner.TSIZE_COL,
                              HiDeFHierarchyRefiner.GENES_COL,
                              HiDeFHierarchyRefiner.STABILITY_COL]
        return node_table

    @staticmethod
    def _get_edge_table_from_hidef(edges_file):
        """
        Takes a HiDeF edges file and creates
        a :py:class:`pandas.DataFrame`

        **Example HiDeF edges file:**

        .. code-block::

            Cluster0-0      Cluster1-0      default
            Cluster0-0      Cluster1-1      default
            Cluster0-0      Cluster1-2      default

        **Resulting DataFrame:**

        .. code-block::

            parent          child           type
            Cluster0-0      Cluster1-0      default
            Cluster0-0      Cluster1-1      default
            Cluster0-0      Cluster1-2      default


        :param edges_file:
        :type edges_file: str
        :return:
        :rtype: :py:class:`pandas.DataFrame`
        """
        edge_table = pd.read_csv(edges_file, header=None, sep='\t')
        edge_table.columns = [HiDeFHierarchyRefiner.PARENT_COL,
                              HiDeFHierarchyRefiner.CHILD_COL,
                              HiDeFHierarchyRefiner.TYPE_COL]
        return edge_table

    @staticmethod
    def _get_node_table_filtered_by_term_size(node_table, min_term_size=4):
        """
        Gets a new :py:class:`pandas.DataFrame` derived from
        **node_table** that only contains rows whose :py:const:`TSIZE_COL`
        is at least **min_term_size**

        :param min_term_size: Minimum size of term (ie number of genes)
        :type min_term_size: int
        :return: Filtered **node_table**
        :rtype: :py:class:`pandas.DataFrame`
        """
        filtered_table = node_table[node_table[HiDeFHierarchyRefiner.TSIZE_COL] >= min_term_size]
        logger.debug('Size node node table after term size filter: ' + str(len(filtered_table)))
        return filtered_table

    @staticmethod
    def _get_edge_table_filtered_by_node_set(edge_table, node_set=None):
        """
        Gets a :py:class:`pandas.DataFrame` derived from **edge_table** that only
        contains rows whose parent and child both exist in **node_set** passed in

        :param edge_table: table with :py:const:`PARENT_COL` and :py:const:`CHILD_COL`
                           columns
        :type edge_table: :py:class:`pandas.DataFrame`
        :param node_set: Names of clusters to keep
        :type node_set: set or list
        :return: edge table with rows whose parent and child both exist in **node_set** passed in
        :rtype: :py:class:`pandas.DataFrame`
        """
        return edge_table[edge_table[[HiDeFHierarchyRefiner.PARENT_COL,
                                      HiDeFHierarchyRefiner.CHILD_COL]].isin(list(node_set)).all(axis=1)]

    @staticmethod
    def _get_leaves_from_edge_table(edge_table=None):
        """
        Gets a set of term names found in :py:const:`CHILD_COL` column values
        that are **NOT** in :py:const:`PARENT_COL` column values

        :param edge_table:
        :type edge_table: :py:class:`pandas.DataFrame`
        :return: leave terms
        :rtype: set
        """
        return (set(edge_table[HiDeFHierarchyRefiner.CHILD_COL].unique())) - set(edge_table[HiDeFHierarchyRefiner.PARENT_COL].unique())

    def _get_leaf_genes_to_add(self, node_table=None, leaves=None):
        """
        For each term in **leaves** list get genes for that term and
        add a list with these elements ``[TERM, GENE NAME, GENE_TYPE]``
        to the list returned

        :param node_table:
        :param leaves: term name
        :type leaves: list
        :return: list of ``[TERM, GENE NAME, GENE_TYPE]`` for all the genes found
                in the terms in **leaves** list
        :rtype: list
        """
        add_gene = []
        for leaf in leaves:
            genes = self._get_genes_from_node_table_for_term(node_table, leaf)
            for gene in genes:
                add_gene.append([leaf, gene, HiDeFHierarchyRefiner.GENE_TYPE])
        return add_gene

    def _get_nonleaf_genes_to_add(self, node_table=None,
                                  edge_table=None):
        """
        # TODO: Test this
        Returns a list of ``[TERM, GENE NAME, GENE_TYPE]`` that
        correspond to genes **NOT** passed to leaf nodes

        :param node_table: HiDeF nodes table
        :type node_table: :py:class:`pandas.DataFrame`
        :param edge_table: HiDeF edge table
        :type edge_table: :py:class:`pandas.DataFrame`
        :return: list of ``[TERM, GENE NAME, GENE_TYPE]`` for all the genes found
                 in non-leaf nodes
        :rtype: list
        """
        gene_rows_to_add = []
        parent_to_child = edge_table.groupby(HiDeFHierarchyRefiner.PARENT_COL)[HiDeFHierarchyRefiner.CHILD_COL].apply(list)  # group the parents
        for parent, children in parent_to_child.iteritems():
            parent_genes = self._get_genes_from_node_table_for_term(node_table, parent)
            child_genes = []
            for child in children:
                genes = self._get_genes_from_node_table_for_term(node_table, child)
                child_genes = set(child_genes).union(set(genes))
            # genes only in parent did not pass to child
            only_parent = set(parent_genes) - set(child_genes)
            if len(only_parent) >= 1:
                for gene in only_parent:
                    gene_rows_to_add.append([parent, gene, HiDeFHierarchyRefiner.GENE_TYPE])
        return gene_rows_to_add

    def _create_ontology(self, node_table=None, edge_table=None, min_term_size=4):
        """
        # TODO: Test this
        Creates ontology from HiDeF nodes and edges file

        :param path: Prefix path to nodes & edges files generated by HiDeF,
                     .nodes and .edges will be appended to this path
        :type path: str
        :param min_term_size:
        :type min_term_size: int
        :return:
        :rtype: py:class:`pandas.DataFrame`
        """
        # filter out rows below minTermSize
        node_table_filtered = self._get_node_table_filtered_by_term_size(node_table,
                                                                         min_term_size=min_term_size)

        logger.info(str(len(node_table_filtered)))
        node_set = set(node_table_filtered[HiDeFHierarchyRefiner.TERMS_COL])  # get the set of nodes

        # keep only edges that have entries in node_set
        edge_table_filtered = self._get_edge_table_filtered_by_node_set(edge_table, node_set=node_set)

        # Find leaves and get their genes
        leaves = self._get_leaves_from_edge_table(edge_table=edge_table_filtered)
        gene_rows_to_add = self._get_leaf_genes_to_add(node_table=node_table_filtered, leaves=leaves)

        # Get non leaf genes
        gene_rows_to_add.extend(self._get_nonleaf_genes_to_add(node_table=node_table_filtered,
                                                               edge_table=edge_table_filtered))

        # add gene rows to new dataframe and append to final dataframe
        add_rows = pd.DataFrame(gene_rows_to_add, columns=[HiDeFHierarchyRefiner.PARENT_COL,
                                                           HiDeFHierarchyRefiner.CHILD_COL,
                                                           HiDeFHierarchyRefiner.TYPE_COL])
        final_df = edge_table_filtered.append(add_rows)
        logger.debug(' Size of final table: ' + str(len(final_df)))
        return final_df

    @staticmethod
    def _get_genes_from_node_table_for_term(nodes_table, term):
        """

        Iterates over genes found under the :py:class:`GENES_COL` column
        splitting by space to get a gene list

        It is assumed the **nodes_table** has this format:

        .. code-block::

            terms           tsize   genes                   stability
            Cluster1-408    4       1528 2310 2666 4273     10
            Cluster1-409    4       126 3366 3794 446       10
            Cluster1-410    4       1522 2733 4334 4542     10


        :param nodes_table: Nodes table from HiDeF output
        :type nodes_table: :py:class:`pandas.DataFrame`
        :param term: term name used to find row to get genes from
        :type term: str
        :return: genes
        :rtype: list
        """
        genes = nodes_table.loc[nodes_table.terms == term][HiDeFHierarchyRefiner.GENES_COL]
        gene_list = []
        for g in genes:
            gene_list.extend(g.split(' '))
        return gene_list

    @staticmethod
    def _to_pandas_dataframe(nx_graph):
        """
        # TODO: Finish implementing this
        Converts **nx_graph** to a Pandas DataFrame
        with columns set to ``source, target, type``

        :param nx_graph:
        :return:
        :rtype: :py:class:`pandas.DataFrame`
        """
        e = nx_graph.edges(data=True)
        df = pd.DataFrame()
        df['source'] = [x[0] for x in e]
        df['target'] = [x[1] for x in e]
        df['type'] = [x[2]['type'] for x in e]
        return df

    @staticmethod
    def _get_term_stats(nx_graph, hiergeneset):
        # TODO: Finish implementing this
        clusters = list(set(list(nx_graph.nodes())) - hiergeneset)
        tsize_list = []
        cgene_list = []
        descendent_list = []
        for c in clusters:
            infoset = nx.descendants(nx_graph, c)
            cgeneset = infoset.intersection(hiergeneset)
            tsize_list.append(len(cgeneset))
            cgene_list.append(list(cgeneset))
            descendent_list.append(list(infoset - cgeneset))
        df = pd.DataFrame(index=clusters)
        df['tsize'] = tsize_list
        df['genes'] = cgene_list
        df['descendent'] = descendent_list
        return df

    @staticmethod
    def _jaccard(a, b):
        """
        Calculates Jaccard index of **a** and **b**

        :param a: set a
        :type a: list or set
        :param b: set b
        :type b: list or set
        :return: Jaccard index
        :rtype: float
        """
        if type(a) != set:
            a = set(a)
        if type(b) != set:
            b = set(b)
        return len(a.intersection(b)) / len(a.union(b))

    @staticmethod
    def _clean_shortcut(self, nx_graph):
        # TODO: Finish implementing this
        edge_df = self._to_pandas_dataframe(nx_graph)
        edge_df.columns = [HiDeFHierarchyRefiner.PARENT_COL,
                           HiDeFHierarchyRefiner.CHILD_COL,
                           HiDeFHierarchyRefiner.TYPE_COL]
        for idx, row in edge_df.iterrows():
            if len(list(nx.all_simple_paths(nx_graph, row[HiDeFHierarchyRefiner.PARENT_COL],
                                            row[HiDeFHierarchyRefiner.CHILD_COL]))) > 1:
                nx_graph.remove_edge(row[HiDeFHierarchyRefiner.PARENT_COL],
                                     row[HiDeFHierarchyRefiner.CHILD_COL])
                logger.debug('shortcut edges is removed between {} and {}'.format(row[HiDeFHierarchyRefiner.PARENT_COL],
                                                                                  row[HiDeFHierarchyRefiner.CHILD_COL]))
        return

    @staticmethod
    def _reorganize(self, nx_graph, hiergeneset, ci_thre): # Add an edge if the nodes have containment index >=threshold
        # TODO: Finish implementing this
        iterate = True
        n_iter = 1
        while iterate:
            clear = True
            logger.debug('... starting iteration ' + str(n_iter))
            ts_df = self._get_term_stats(nx_graph, hiergeneset) # get the termStats from the networkx
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
                        logger.debug('{} is contained in {} with a CI bigger than threshold, add edge between'.format(tmp_comp, comp))
                        nx_graph.add_edge(comp, tmp_comp, type='default')
                        clear = False
                        descendent += tmp_row['descendent']
            # Further clean up using networkx to remove shortcut edges
            self._clean_shortcut(nx_graph)
            # Update variables
            n_iter += 1
            if clear:
                iterate = False
        if n_iter == 2:
            modified = False
        else:
            modified = True
        return modified

    def _merge_parent_child(self, nx_graph, hiergeneset, ji_thre):
        # TODO: Finish implementing this
        # Delete child term if highly similar with parent term
        # One parent-child relationship at a time to avoid complicacies involved in potential long tail
        logger.debug('... start removing highly similar parent-child relationship')
        similar = True
        merged = False
        while similar:
            clear = True
            edge_df = self._to_pandas_dataframe(nx_graph)
            ts_df = self._get_term_stats(nx_graph, hiergeneset)
            default_edge = edge_df[edge_df['type'] == 'default'] # edges
            for idx, row in default_edge.iterrows():
                if self._jaccard(ts_df.loc[row['source']]['genes'], ts_df.loc[row['target']]['genes']) >= ji_thre:
                    logger.debug('# Cluster pair {}->{} failed Jaccard, removing cluster {}'.format(row['source'], row['target'],
                                                                                             row['target']))
                    clear = False
                    merged = True
                    parents = edge_df[edge_df['target'] == row['target']]['source'].values
                    children = edge_df[edge_df['source'] == row['target']]['target'].values
                    # Remove all parent->node edges
                    for pnode in parents:
                        nx_graph.remove_edge(pnode, row['target'])
                    for child_node in children:
                        etype = nx_graph[row['target']][child_node]['type']
                        # Remove all node->child edges
                        nx_graph.remove_edge(row['target'], child_node)
                        # Add all parent->child edges
                        for pnode in parents:
                            nx_graph.add_edge(pnode, child_node, type=etype)
                    # Remove target node
                    nx_graph.remove_node(row['target'])
                    break
            if clear:
                similar = False
        # Clean up shortcuts introduced during node deleteing process
        self._clean_shortcut(nx_graph)
        return merged

    def _collapse_redundant(self, nx_graph, hiergeneset, min_diff):
        # TODO: Finish implementing this
        # Delete child term if highly similar with parent term
        # One parent-child relationship at a time to avoid complicacies involved in potential long tail
        logger.debug('... start removing highly redundant systems')
        while True:
            edge_df = self._to_pandas_dataframe(nx_graph)
            ts_df = self._get_term_stats(nx_graph, hiergeneset)
            default_edge = edge_df[edge_df['type'] == 'default']
            to_collapse = []
            for idx, row in default_edge.iterrows():
                parentSys, childSys, _ = row.values
                if ts_df.loc[parentSys]['tsize'] - ts_df.loc[childSys]['tsize'] < min_diff:
                    to_collapse.append([parentSys, childSys])
            if len(to_collapse) == 0:
                logger.debug('nothing to collapse')
                return
            to_collapse = pd.DataFrame(to_collapse, columns=['parent', 'child'])
            deleteSys = to_collapse.loc['child']
            logger.debug('# Cluster pair {}->{} highly redundant, removing cluster {}'.format(to_collapse.loc['parent'],
                                                                                       to_collapse.loc['child'],
                                                                                       deleteSys))
            parents = edge_df[edge_df['target'] == deleteSys]['source'].values
            children = edge_df[edge_df['source'] == deleteSys]['target'].values
            # Remove all parent->node edges
            for pnode in parents:
                nx_graph.remove_edge(pnode, deleteSys)
            for child_node in children:
                etype = nx_graph[deleteSys][child_node]['type']
                # Remove all node->child edges
                nx_graph.remove_edge(deleteSys, child_node)
                # Add all parent->child edges
                for pnode in parents:
                    nx_graph.add_edge(pnode, child_node, type=etype)
            # Remove target node
            nx_graph.remove_node(deleteSys)

    def refine_hierarchy(self, outprefix=None,
                         align_ont_path=None):
        """
        # TODO: Finish implementing this

        :param outprefix: output_dir/file_prefix for the output file
        :param ci_thre: Containment index threshold
        :param ji_thre: Jaccard index threshold for merging similar clusters
        :param min_system_size: Minimum number of proteins requiring each system to have
        :param min_diff: Minimum difference in number of proteins for every parent-child pair
        :param align_ont_path: Full path to alignOntology
        :return:
        """
        logger.debug('Containment index threshold: ' + str(self._ci_thre))
        logger.debug('Jaccard index threshold: ' + str(self._ji_thre))

        # Read node table
        node_table = self._get_node_table_from_hidef(outprefix,
                                                     HiDeFHierarchyRefiner.NODES_SUFFIX)

        # Read edge table
        edge_table = self._get_edge_table_from_hidef(outprefix + HiDeFHierarchyRefiner.EDGES_SUFFIX)

        ont = self._create_ontology(node_table=node_table, edge_table=edge_table,
                                    min_term_size=self._min_term_size)
        hiergeneset = set(ont[ont[HiDeFHierarchyRefiner.TYPE_COL] == HiDeFHierarchyRefiner.GENE_TYPE][HiDeFHierarchyRefiner.CHILD_COL].values)

        nx_graph = nx.from_pandas_edgelist(ont,
                                           source=HiDeFHierarchyRefiner.PARENT_COL,
                                           target=HiDeFHierarchyRefiner.CHILD_COL,
                                    edge_attr=HiDeFHierarchyRefiner.TYPE_COL,
                                    create_using=nx.DiGraph())

        if not nx.is_directed_acyclic_graph(nx_graph):
            raise ValueError('Input hierarchy is not DAG!')

        while True:
            modified = self._reorganize(nx_graph, hiergeneset, self._ci_thre)
            merged = self._merge_parent_child(nx_graph, hiergeneset, self._ji_thre)
            if not modified and not merged:
                break

        self._collapse_redundant(nx_graph, hiergeneset, self._min_diff)
        # Output as ddot edge file
        self._clean_shortcut(nx_graph)
        edge_df = self._to_pandas_dataframe(nx_graph)
        edge_df.to_csv('{}.pruned.ont'.format(outprefix), header=False, index=False, sep='\t')

        # TODO: Replace ontologyTermStats with native python code
        run_termStats = '{}/ontologyTermStats {} genes > {}'.format(align_ont_path,
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
        nodes.sort_values(by='Size', ascending=False, inplace=True)
        nodes.to_csv(outprefix+'.pruned.nodes', header=False, sep='\t')

        edges = edge_df.loc[edge_df['type'] == 'default', :]
        edges.to_csv(outprefix+'.pruned.edges', sep='\t', header=None,index=None)

        logger.debug('Number of edges is ' + str(len(edges)) + ', number of nodes are ' + str(len(nodes)))


