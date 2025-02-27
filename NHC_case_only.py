# python3.8
__author__ = "Peng Zhang"
__copyright__ = "Copyright 2021, St. Giles Laboratory of Human Genetics of Infectious Diseases, The Rocefeller Unversity"
__license__ = "CC BY-NC-ND 4.0"
__version__ = "verion-2, 2023-04"
import os
import time
import argparse
from scipy import stats
from decimal import Decimal
from collections import defaultdict

###
# input parameters
###
print('#######################################')
print('   ###    ##   ##     ##     ######    ')
print('   ## #   ##   ##     ##    ##    ##   ')
print('   ##  #  ##   #########   ##          ')
print('   ##   # ##   ##     ##    ##    ##   ')
print('   ##    ###   ##     ##     ######    ')
print(' Network-based Heterogenity Clustering ')
print('              (case only)              ')
print('#######################################')

global_start = time.time()
parser = argparse.ArgumentParser(description="Network-based Heterogenity Clustering (Case Only)")
parser.add_argument("-case", "--case", help="gene list in case cohort")
parser.add_argument("-w", "--edgeweight", type=float, default=0.99, help="edge weight cutoff [0.7~1], default=0.99")
parser.add_argument("-b", "--hub", type=int, default=100, help="remove hub genes with high connectivity (default=100). Use 0 to include all genes.")
parser.add_argument("-m", "--merge", type=float, default=0.5, help="merge overlapped gene clusters [0~1], default=0.5")
parser.add_argument("-o", "--output", help="output filename")

args = parser.parse_args()
case_input = args.case
edge_weight_cutoff = args.edgeweight
hub_cutoff = args.hub
cluster_merge_cutoff = args.merge
case_filename = case_input[0:case_input.rfind('.')]
output_filename = args.output
if not output_filename:
	output_filename = 'output_case_only_' + str(int(time.time())) + '.txt'

###
# loading data
###
print('>> Loading Data')

file_case_gene_list = open(case_input, 'r')
file_case_gene_list.readline()
case_size = 0
case_list = []
case_genes = set()
case_gene_set_dict = defaultdict(set)
for eachline in file_case_gene_list:
	item = eachline.strip().split('\t')
	case = item[0]
	gene_set = set(item[1].split(','))
	case_list.append(case)
	case_genes = case_genes | gene_set
	case_gene_set_dict[case] = gene_set
	case_size += 1

file_connectivity = open('Data_NHC_Connectivity.txt', 'r')
hub_genes = set()
for eachline in file_connectivity:
	item = eachline.strip().split('\t')
	gene = item[0]
	connectivity = int(item[1])
	if connectivity >= hub_cutoff:
		hub_genes.add(gene)

file_network = open('Data_NHC_Network.txt', 'r')
case_network = dict()
for eachline in file_network:
	item = eachline.strip().split('\t')
	geneA = item[0]
	geneB = item[1]
	gene_pair = (geneA, geneB)
	edge_weight = float(item[2])
	if (geneA in case_genes) and (geneB in case_genes) and (edge_weight >= edge_weight_cutoff):
		if hub_cutoff == 0:
			case_network[gene_pair] = edge_weight
		else:
			if (geneA not in hub_genes) and (geneB not in hub_genes):
				case_network[gene_pair] = edge_weight

file_pathway = open('Data_NHC_Pathway.txt', 'r')
pathway_size = 0
pathway_genes = set()
pathway_gene_set_dict = dict()
for eachline in file_pathway:
	item = eachline.strip().split('\t')
	pathway = item[0]
	gene_set = set(item[1].split(','))
	pathway_genes = pathway_genes | gene_set
	pathway_gene_set_dict[pathway] = gene_set
	pathway_size += 1

file_GO_BP = open('Data_NHC_GO_BP.txt', 'r')
GO_BP_size = 0
GO_BP_genes = set()
GO_BP_gene_set_dict = dict()
for eachline in file_GO_BP:
	item = eachline.strip().split('\t')
	GO_BP = item[0]
	gene_set = set(item[2].split(','))
	GO_BP_genes = GO_BP_genes | gene_set
	GO_BP_gene_set_dict[GO_BP] = gene_set
	GO_BP_size += 1

file_GO_MF = open('Data_NHC_GO_MF.txt', 'r')
GO_MF_size = 0
GO_MF_genes = set()
GO_MF_gene_set_dict = dict()
for eachline in file_GO_MF:
	item = eachline.strip().split('\t')
	GO_MF = item[0]
	gene_set = set(item[2].split(','))
	GO_MF_genes = GO_MF_genes | gene_set
	GO_MF_gene_set_dict[GO_MF] = gene_set
	GO_MF_size += 1


###
# gene clustering
###
print('>> Gene Clustering')
global_clusters = set()
global_cluster_result = []
file_out_initial = open('temp_clusters_initial.txt', 'w')


# function for gene clustering
def gene_clustering(cur_index):
	cur_case = case_list[cur_index]
	cur_case_gene_set = case_gene_set_dict[cur_case]

	for cur_gene in cur_case_gene_set:
		this_gene_set = set()
		this_gene_set.add(cur_gene)
		this_case_set = set()
		this_case_set.add(cur_case)

		checking_index_set = set(range(len(case_list)))
		checking_index_set.remove(cur_index)
		while checking_index_set:
			closest_index = -1
			closest_case = ''
			closest_gene = ''
			overlap = False
			highest_edge_weight = 0

			for checking_index in checking_index_set:
				checking_case = case_list[checking_index]
				checking_gene_set = case_gene_set_dict[checking_case]
				overlapping_gene_set = this_gene_set & checking_gene_set

				if overlapping_gene_set:
					closest_index = checking_index
					closest_case = checking_case
					overlap = True
					break

				else:
					for existing_gene in this_gene_set:
						for checking_gene in checking_gene_set:
							if existing_gene < checking_gene:
								checking_pair = (existing_gene, checking_gene)
							else:
								checking_pair = (checking_gene, existing_gene)
							temp_edge_weight = 0
							if checking_pair in case_network.keys():
								temp_edge_weight = case_network[checking_pair]
							if temp_edge_weight > highest_edge_weight:
								closest_index = checking_index
								closest_case = checking_case
								closest_gene = checking_gene
								highest_edge_weight = temp_edge_weight

			if overlap:
				checking_index_set.remove(closest_index)
				this_case_set.add(closest_case)
			elif closest_index != -1:
				checking_index_set.remove(closest_index)
				this_case_set.add(closest_case)
				this_gene_set.add(closest_gene)
			else:
				break

		if len(this_gene_set) > 2:
			this_cluster_gene_list = list(this_gene_set)
			this_cluster_gene_list.sort()
			this_cluster_gene_output = ','.join(this_cluster_gene_list)

			this_cluster_case_list = list(this_case_set)
			this_cluster_case_list.sort()
			this_cluster_case_output = ','.join(this_cluster_case_list)

			if this_cluster_gene_output not in global_clusters:
				global_clusters.add(this_cluster_gene_output)
				this_cluster = list()
				this_cluster.append(len(this_gene_set))
				this_cluster.append(len(this_case_set))
				this_cluster.append(this_cluster_gene_output)
				this_cluster.append(this_cluster_case_output)
				global_cluster_result.append(this_cluster)


for case_i in range(len(case_list)):
	start = time.time()
	gene_clustering(case_i)
	end = time.time()
	timecost = str(int(end - start))
	print('>> Clustering', str(case_i+1)+'/'+str(case_size), case_list[case_i], timecost, 'sec')
print('>> # Gene Clusters (initial):', str(len(global_cluster_result)))

for each_cluster in global_cluster_result:
	file_out_initial.write(str(each_cluster[0]) + '\t')
	file_out_initial.write(str(each_cluster[1]) + '\t')
	file_out_initial.write(str(each_cluster[2]) + '\t')
	file_out_initial.write(str(each_cluster[3]) + '\n')
file_out_initial.close()


###
# gene cluster merging
###
file_out_merged = open('temp_clusters_merged.txt', 'w')

# load the initial gene clusters
gene_cluster_merging = []
case_cluster_merging = []
for each_cluster in global_cluster_result:
	gene_cluster_merging.append(set(each_cluster[2].split(',')))
	case_cluster_merging.append(set(each_cluster[3].split(',')))

# iteratively merge gene clusters above cluster_merge_cutoff
stable = False
while not stable:
	N = len(gene_cluster_merging)
	overlap_max = 0
	overlap_max_pair = [-1, -1]
	overlap_all_in = False
	for i in range(0, N):
		for j in range(i+1, N):
			if gene_cluster_merging[i].issubset(gene_cluster_merging[j]):
				overlap_max_pair = [i, j]
				overlap_max = 1
			elif gene_cluster_merging[j].issubset(gene_cluster_merging[i]):
				overlap_max_pair = [i, j]
				overlap_max = 1
			else:
				intersect = len(gene_cluster_merging[i] & gene_cluster_merging[j])
				union = len(gene_cluster_merging[i] | gene_cluster_merging[j])
				overlap_ratio = round(float(intersect) / float(union), 3)
				if overlap_ratio > overlap_max:
					overlap_max_pair = [i, j]
					overlap_max = overlap_ratio

	if overlap_max >= cluster_merge_cutoff:
		stable = False
		max_i = overlap_max_pair[0]
		max_j = overlap_max_pair[1]

		# adding: gene_cluster_merging, case_cluster_merging
		new_gene_cluster_merging = gene_cluster_merging[max_i] | gene_cluster_merging[max_j]
		gene_cluster_merging.append(new_gene_cluster_merging)
		gene_cluster_merging[max_i] = set()
		gene_cluster_merging[max_j] = set()

		new_case_cluster_merging = case_cluster_merging[max_i] | case_cluster_merging[max_j]
		case_cluster_merging.append(new_case_cluster_merging)
		case_cluster_merging[max_i] = set()
		case_cluster_merging[max_j] = set()

		# updating: gene_cluster_merging, case_cluster_merging
		temp_gene_cluster_merging = []
		for each_gene_cluster_merging in gene_cluster_merging:
			if each_gene_cluster_merging:
				temp_gene_cluster_merging.append(each_gene_cluster_merging)
		gene_cluster_merging = temp_gene_cluster_merging

		temp_case_cluster_merging = []
		for each_case_cluster_merging in case_cluster_merging:
			if each_case_cluster_merging:
				temp_case_cluster_merging.append(each_case_cluster_merging)
		case_cluster_merging = temp_case_cluster_merging

	else:
		stable = True

if stable:
	for k in range(0, len(gene_cluster_merging)):
		this_gene_cluster_list = list(gene_cluster_merging[k])
		this_gene_cluster_list.sort()
		this_case_cluster_list = list(case_cluster_merging[k])
		this_case_cluster_list.sort()

		file_out_merged.write(str(len(this_gene_cluster_list)) + '\t')
		file_out_merged.write(str(len(this_case_cluster_list)) + '\t')
		file_out_merged.write(','.join(this_gene_cluster_list) + '\t')
		file_out_merged.write(','.join(this_case_cluster_list) + '\n')
print('>> # Gene Clusters (merged):', str(len(gene_cluster_merging)))
file_out_merged.close()


###
# pathway enrichment
###
file_in_merged = open('temp_clusters_merged.txt', 'r')
file_out = open(output_filename, 'w')
file_out.write('Cluster_ID\t#Genes\t#Cases\tGene_Cluster\tCase_Cluster\t')
file_out.write('#Pathways\tPathway_List\tTop_Pathway\tGO_BP_List\tGO_MF_List\n')

cluster_id = 0
gene_cluster_enriched = 0
for eachline in file_in_merged:
	cluster_id += 1
	file_out.write('Cluster_' + str(cluster_id) + '\t' + eachline.strip() + '\t')
	item = eachline.strip().split('\t')
	this_case_gene_set = set(item[2].split(','))

	# pathway enrichment
	this_case_pathway_hit = dict()
	for each_pathway in pathway_gene_set_dict.keys():
		pathway_gene_set = pathway_gene_set_dict[each_pathway]
		case_pathway_overlap = this_case_gene_set & pathway_gene_set
		case_in = len(case_pathway_overlap)
		case_out = len(this_case_gene_set) - case_in
		pathway_in = len(pathway_gene_set)
		pathway_out = len(pathway_genes) - pathway_in
		if case_in != 0:
			odd, pvalue = stats.fisher_exact([[case_in, case_out], [pathway_in, pathway_out]], alternative='two-sided')
			adj_pvalue = pvalue * pathway_size
			if adj_pvalue < 0.00001:
				adj_pvalue = float('%.3E' % Decimal(adj_pvalue))
				this_case_pathway_hit[each_pathway] = adj_pvalue

	# enriched pathway output
	pathway_count = 0
	pathway_output = top_pathway_name = top_pathway_pvalue = '.'
	if len(this_case_pathway_hit) > 0:
		gene_cluster_enriched += 1
		pathway_count = len(this_case_pathway_hit)
		pathway_pvalue_sorted = sorted(this_case_pathway_hit.items(), key=lambda x: x[1])
		top = True
		pathway_output = ''
		for each_sorted in pathway_pvalue_sorted:
			pathway_name = each_sorted[0]
			pathway_pvalue = each_sorted[1]
			pathway_output += pathway_name + '(' + str(pathway_pvalue) + '),'
			if top:
				top_pathway_name = pathway_name
				top_pathway_pvalue = str(pathway_pvalue)
				top = False
		pathway_output = pathway_output[0:-1]
		file_out.write(str(pathway_count)+'\t'+pathway_output+'\t'+top_pathway_name+'('+top_pathway_pvalue+')\t')
	else:
		file_out.write('0\t.\t.\t')

	# GO BP enrichment
	this_case_GO_BP_hit = dict()
	for each_GO_BP in GO_BP_gene_set_dict.keys():
		GO_BP_gene_set = GO_BP_gene_set_dict[each_GO_BP]
		case_GO_BP_overlap = this_case_gene_set & GO_BP_gene_set
		case_in = len(case_GO_BP_overlap)
		case_out = len(this_case_gene_set) - case_in
		GO_BP_in = len(GO_BP_gene_set)
		GO_BP_out = len(GO_BP_genes) - GO_BP_in
		if case_in != 0:
			odd, pvalue = stats.fisher_exact([[case_in, case_out], [GO_BP_in, GO_BP_out]], alternative='two-sided')
			adj_pvalue = pvalue * GO_BP_size
			if adj_pvalue < 0.00001:
				adj_pvalue = float('%.3E' % Decimal(adj_pvalue))
				this_case_GO_BP_hit[each_GO_BP] = adj_pvalue

	# enriched GO_BP output
	GO_BP_output = '.'
	if len(this_case_GO_BP_hit) > 0:
		GO_BP_pvalue_sorted = sorted(this_case_GO_BP_hit.items(), key=lambda x: x[1])
		GO_BP_output = ''
		for each_sorted in GO_BP_pvalue_sorted:
			GO_BP_name = each_sorted[0]
			GO_BP_pvalue = each_sorted[1]
			GO_BP_output += GO_BP_name + '(' + str(GO_BP_pvalue) + '),'
		GO_BP_output = GO_BP_output[0:-1]
	file_out.write(GO_BP_output+'\t')

	# GO MF enrichment
	this_case_GO_MF_hit = dict()
	for each_GO_MF in GO_MF_gene_set_dict.keys():
		GO_MF_gene_set = GO_MF_gene_set_dict[each_GO_MF]
		case_GO_MF_overlap = this_case_gene_set & GO_MF_gene_set
		case_in = len(case_GO_MF_overlap)
		case_out = len(this_case_gene_set) - case_in
		GO_MF_in = len(GO_MF_gene_set)
		GO_MF_out = len(GO_MF_genes) - GO_MF_in
		if case_in != 0:
			odd, pvalue = stats.fisher_exact([[case_in, case_out], [GO_MF_in, GO_MF_out]], alternative='two-sided')
			adj_pvalue = pvalue * GO_MF_size
			if adj_pvalue < 0.00001:
				adj_pvalue = float('%.3E' % Decimal(adj_pvalue))
				this_case_GO_MF_hit[each_GO_MF] = adj_pvalue

	# enriched GO_MF output
	GO_MF_output = '.'
	if len(this_case_GO_MF_hit) > 0:
		GO_MF_pvalue_sorted = sorted(this_case_GO_MF_hit.items(), key=lambda x: x[1])
		GO_MF_output = ''
		for each_sorted in GO_MF_pvalue_sorted:
			GO_MF_name = each_sorted[0]
			GO_MF_pvalue = each_sorted[1]
			GO_MF_output += GO_MF_name + '(' + str(GO_MF_pvalue) + '),'
		GO_MF_output = GO_MF_output[0:-1]
	file_out.write(GO_MF_output+'\n')

print('>> # Gene Clusters (pathway enriched):', str(gene_cluster_enriched))
os.remove('temp_clusters_initial.txt')
os.remove('temp_clusters_merged.txt')
file_out.close()

global_end = time.time()
global_timecost = int(global_end - global_start)
print('>> Total Time Cost:', str(global_timecost), 'sec')
