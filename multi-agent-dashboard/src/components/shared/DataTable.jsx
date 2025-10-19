import React, { useState, useMemo } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Search,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react'

const DataTable = ({
  data = [],
  columns = [],
  searchable = true,
  filterable = true,
  sortable = true,
  exportable = true,
  refreshable = true,
  onRefresh,
  onRowClick,
  pageSize = 10,
  loading = false,
  emptyMessage = 'No data available'
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })
  const [filterConfig, setFilterConfig] = useState({})
  const [currentPage, setCurrentPage] = useState(1)

  // Get filterable columns
  const filterableColumns = useMemo(() => 
    columns.filter(col => col.filterable),
    [columns]
  )

  // Apply search
  const searchedData = useMemo(() => {
    if (!searchTerm) return data

    return data.filter(row =>
      columns.some(col => {
        const value = row[col.key]
        return value?.toString().toLowerCase().includes(searchTerm.toLowerCase())
      })
    )
  }, [data, searchTerm, columns])

  // Apply filters
  const filteredData = useMemo(() => {
    let result = searchedData

    Object.entries(filterConfig).forEach(([key, value]) => {
      if (value && value !== 'all') {
        result = result.filter(row => row[key] === value)
      }
    })

    return result
  }, [searchedData, filterConfig])

  // Apply sorting
  const sortedData = useMemo(() => {
    if (!sortConfig.key) return filteredData

    return [...filteredData].sort((a, b) => {
      const aVal = a[sortConfig.key]
      const bVal = b[sortConfig.key]

      if (aVal === bVal) return 0

      const comparison = aVal < bVal ? -1 : 1
      return sortConfig.direction === 'asc' ? comparison : -comparison
    })
  }, [filteredData, sortConfig])

  // Pagination
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return sortedData.slice(start, start + pageSize)
  }, [sortedData, currentPage, pageSize])

  const totalPages = Math.ceil(sortedData.length / pageSize)

  // Handle sort
  const handleSort = (key) => {
    if (!sortable) return

    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }))
  }

  // Handle filter change
  const handleFilterChange = (key, value) => {
    setFilterConfig(prev => ({ ...prev, [key]: value }))
    setCurrentPage(1)
  }

  // Export to CSV
  const exportToCSV = () => {
    const headers = columns.map(col => col.header).join(',')
    const rows = sortedData.map(row =>
      columns.map(col => {
        const value = row[col.key]
        return typeof value === 'string' && value.includes(',') 
          ? `"${value}"` 
          : value
      }).join(',')
    ).join('\n')

    const csv = `${headers}\n${rows}`
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `export-${Date.now()}.csv`
    a.click()
  }

  // Render cell content
  const renderCell = (row, column) => {
    const value = row[column.key]

    if (column.render) {
      return column.render(value, row)
    }

    if (column.type === 'badge') {
      return <Badge variant={column.badgeVariant?.(value)}>{value}</Badge>
    }

    if (column.type === 'date') {
      return new Date(value).toLocaleDateString()
    }

    if (column.type === 'datetime') {
      return new Date(value).toLocaleString()
    }

    if (column.type === 'currency') {
      return new Intl.NumberFormat('en-US', { 
        style: 'currency', 
        currency: 'USD' 
      }).format(value)
    }

    return value
  }

  // Get unique values for filter
  const getUniqueValues = (key) => {
    const values = [...new Set(data.map(row => row[key]))]
    return values.filter(Boolean)
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between space-x-4">
        {/* Search */}
        {searchable && (
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        )}

        {/* Filters */}
        {filterable && filterableColumns.length > 0 && (
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            {filterableColumns.map(col => (
              <Select
                key={col.key}
                value={filterConfig[col.key] || 'all'}
                onValueChange={(value) => handleFilterChange(col.key, value)}
              >
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder={`Filter ${col.header}`} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All {col.header}</SelectItem>
                  {getUniqueValues(col.key).map(value => (
                    <SelectItem key={value} value={value}>
                      {value}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center space-x-2">
          {refreshable && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          )}
          {exportable && (
            <Button
              variant="outline"
              size="sm"
              onClick={exportToCSV}
            >
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map(column => (
                <TableHead
                  key={column.key}
                  className={sortable && column.sortable !== false ? 'cursor-pointer select-none' : ''}
                  onClick={() => column.sortable !== false && handleSort(column.key)}
                >
                  <div className="flex items-center space-x-2">
                    <span>{column.header}</span>
                    {sortable && column.sortable !== false && (
                      <span className="ml-auto">
                        {sortConfig.key === column.key ? (
                          sortConfig.direction === 'asc' ? (
                            <ArrowUp className="w-4 h-4" />
                          ) : (
                            <ArrowDown className="w-4 h-4" />
                          )
                        ) : (
                          <ArrowUpDown className="w-4 h-4 text-gray-400" />
                        )}
                      </span>
                    )}
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="text-center py-8">
                  <div className="flex items-center justify-center space-x-2">
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    <span>Loading...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : paginatedData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="text-center py-8 text-gray-500">
                  {emptyMessage}
                </TableCell>
              </TableRow>
            ) : (
              paginatedData.map((row, index) => (
                <TableRow
                  key={row.id || index}
                  className={onRowClick ? 'cursor-pointer hover:bg-gray-50' : ''}
                  onClick={() => onRowClick?.(row)}
                >
                  {columns.map(column => (
                    <TableCell key={column.key}>
                      {renderCell(row, column)}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, sortedData.length)} of {sortedData.length} results
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
            >
              Previous
            </Button>
            <div className="flex items-center space-x-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1)
                .filter(page => {
                  // Show first, last, current, and adjacent pages
                  return page === 1 || 
                         page === totalPages || 
                         Math.abs(page - currentPage) <= 1
                })
                .map((page, index, array) => (
                  <React.Fragment key={page}>
                    {index > 0 && array[index - 1] !== page - 1 && (
                      <span className="px-2">...</span>
                    )}
                    <Button
                      variant={currentPage === page ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setCurrentPage(page)}
                    >
                      {page}
                    </Button>
                  </React.Fragment>
                ))}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default DataTable

