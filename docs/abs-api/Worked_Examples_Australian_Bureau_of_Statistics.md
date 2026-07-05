# Worked Examples | Australian Bureau of Statistics

Dataflows are how we look at the data in the ABS API, but there's another structure that defines how the data is structured (which is super important for querying it and understanding the response). This is pretty appropriately called the Data Structure Definition, or DSD for short. If we’re thinking of a dataflow as a table, we can think about DSDs as the definition of what rows and columns there are in the table, and what values they can take (along with additional metadata).

What has this got to do with getting the data? It's important to know how the data is structured so we can build a query. Now, our dataflow is pretty small, so we could just get all the data and deal with finding the value we want... but some of the other dataflows are very large. So we should learn how to query the API to avoid getting a whole bunch of data we don't want, crashing our computer or exceeding the size limits for the API.

Data queries to the API look like this: https://data.api.abs.gov.au/rest/data/{flowRef}/{dataKey}?{queryParameters}. We're going to need to provide a flowRef so the API knows what dataflow to get data from, and a dataKey to filter the data we get back. We'll leave the extra parameters to the next section.

#### FlowRef

There's a few ways we can define the flowRef, but we'll be using the simplest one. From the first request we made above we know Dataflow id=“ALC” therefore our flowRef is ALC

#### dataKey

The dataKey section of the URL lets us tell the ABS API that we only want a subset of the available data. We do that by providing the values we want from each dimension, separated by a period "." character. You can think of the dimensions as the columns and rows of the table defined by the DSD. So, this is why we need to look at the DSD our dataflow is using. Firstly, we need to know what order the dimensions appear in the DSD, because that's the order we need to put them in the dataKey. Secondly, we need to know what values are available, and which ones correspond to the information I want to retrieve.

Each of the dimensions in our dataflow's DSD is represented by a codelist. So we need to look at the DSD and see what order the dimensions are (and what they are) and then look at each of the codelists and work out what code corresponds to the information we want (remember, it's how much mid-strength beer each Australian drank in 2008).

Now, we can use the same URL we used for the dataflow (because DSDs also have their own endpoint), but let’s go one step further and get a specific DSD instead of all of them. To do that we need to know how to tell the API which DSD we want. There are three pieces of information that together let us uniquely identify a dataflow or a DSD (or any maintainable structure for that matter):

-   The agency id: This is who owns the structure, and in the ABS API it's always the ABS... so it's ABS

-   The structure id itself
-   The version number of the structure: this is used when structures need to change over time. A classic example would be adding a country to the list of countries... the old list will still be around, but we'll create a new version of it

Now, we don't actually have to provide a version number for our DSD, because if you don't give one, the API assumes you just want the latest one. The question now is where to get the structure id for the DSD for our dataflow. Well, luckily we've already seen it, when we were looking for our dataflow in step 1 above.

```
<structure:Structure>
  <Ref id="ALC" version="1.0.0" agencyID="ABS" package="datastructure" class="DataStructure"/>
</structure:Structure>
```

Given this, we can get the DSD using the url: [https://data.api.abs.gov.au/rest/datastructure/ABS/ALC](https://data.api.abs.gov.au/rest/datastructure/ABS/ALC)

```
<message:Structures>
   <structure:DataStructures>
      <structure:DataStructure id="ALC" agencyID="ABS" version="1.0.0" isFinal="true">
         <common:Name xml:lang="en">Apparent Consumption of Alcohol, Australia</common:Name>
         <structure:DataStructureComponents>
            <structure:DimensionList id="DimensionDescriptor">
               <structure:Dimension id="TYP" position="1">
                  <structure:ConceptIdentity>
                     <Ref id="TYP" maintainableParentID="CS_ALC" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept" />
                  </structure:ConceptIdentity>
                  <structure:LocalRepresentation>
                     <structure:Enumeration>
                        <Ref id="CL_ALC_TYP" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist" />
                     </structure:Enumeration>
                  </structure:LocalRepresentation>
               </structure:Dimension>
               <structure:Dimension id="MEA" position="2">
                  <structure:ConceptIdentity>
                     <Ref id="MEASURE" maintainableParentID="CS_COMMON" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept" />
                  </structure:ConceptIdentity>
                  <structure:LocalRepresentation>
                     <structure:Enumeration>
                        <Ref id="CL_ALC_MEASURE" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist" />
                     </structure:Enumeration>
                  </structure:LocalRepresentation>
               </structure:Dimension>
```

This gives us the Data Structure with dimensions. The order of dimensions is given by their position eg. position="1".

But, we don't just need to know the order of the dimensions, but what values they take. That's defined by the codelist each dimension uses. Now, we could do the same sort of thing we did with getting to the DSD from the dataflow. Each dimension will refer to a codelist like we can see above for the codelist CL\_ALC\_TYP.

We could call the API to get each of the codelists in turn using URLs like [https://data.api.abs.gov.au/rest/codelist/ABS/CL\_ALC\_TYP/1.0.0](https://data.api.abs.gov.au/rest/codelist/ABS/CL_ALC_TYP/1.0.0) (we included the version number 1.0.0 here). But that means we have to make a call for every dimension. Let’s save time and use our first query parameter when getting structure information: references. This parameter lets us retrieve not just the specified structure from the API, but some of the structures it references as well. We're going to specify the value codelist, telling the API that we want to retrieve any codelists referred to by our DSD: [https://data.api.abs.gov.au/rest/datastructure/ABS/ALC?references=codelist](https://data.api.abs.gov.au/rest/datastructure/ABS/ALC?references=codelist) (Some codelists removed for brevity):

```
<message:Structures>
   <structure:Codelists>
      <structure:Codelist id="CL_ALC_BEVT" agencyID="ABS" version="1.0.0" isFinal="true">
         <common:Name xml:lang="en">Beverage Type</common:Name>
         <structure:Code id="1">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">1</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Beer</common:Name>
         </structure:Code>
         <structure:Code id="2">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">2</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Wine</common:Name>
         </structure:Code>
         <structure:Code id="3">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">3</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Spirits and RTDs</common:Name>
         </structure:Code>
         <structure:Code id="4">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">4</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Total all beverages</common:Name>
         </structure:Code>
         <structure:Code id="5">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">5</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Cider</common:Name>
         </structure:Code>
      </structure:Codelist>
      <structure:Codelist id="CL_ALC_MEASURE" agencyID="ABS" version="1.0.0" isFinal="true">
         <common:Name xml:lang="en">Measure</common:Name>
         <structure:Code id="1">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">1</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Total apparent consumption ('000 litres)</common:Name>
         </structure:Code>
         <structure:Code id="2">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">2</common:AnnotationText>
               </common:Annotation>
               <common:Annotation>
                  <common:AnnotationType>FURTHER_INFORMATION</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">Litres per person aged 15 years and over</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Per capita apparent consumption (litres)</common:Name>
         </structure:Code>
      </structure:Codelist>
      <structure:Codelist id="CL_ALC_SUB" agencyID="ABS" version="1.0.0" isFinal="true">
         <common:Name xml:lang="en">Beverage Subtype/Strength</common:Name>
         <structure:Code id="1">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">1</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Low alcohol beer</common:Name>
         </structure:Code>
         <structure:Code id="2">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">2</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Other alcohol beer</common:Name>
         </structure:Code>
         <structure:Code id="3">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">3</common:AnnotationText>
               </common:Annotation>
               <common:Annotation>
                  <common:AnnotationType>FURTHER_INFORMATION</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">Alcohol volume of low strength beer is greater than 1.15% and less than or equal to 3.0%</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Low strength beer</common:Name>
         </structure:Code>
         <structure:Code id="4">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">4</common:AnnotationText>
               </common:Annotation>
               <common:Annotation>
                  <common:AnnotationType>FURTHER_INFORMATION</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">Alcohol volume of mid strength beer is greater than 3.0% and less than or equal to 3.5%</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Mid strength beer</common:Name>
         </structure:Code>
         <structure:Code id="5">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">5</common:AnnotationText>
               </common:Annotation>
               <common:Annotation>
                  <common:AnnotationType>FURTHER_INFORMATION</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">Alcohol volume of full strength beer is greater than 3.5%</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Full strength beer</common:Name>
         </structure:Code>
         <structure:Code id="6">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">6</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Total beer</common:Name>
         </structure:Code>
         <structure:Code id="7">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">7</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">White table wine</common:Name>
         </structure:Code>
         <structure:Code id="8">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">8</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Red table wine</common:Name>
         </structure:Code>
         <structure:Code id="9">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">9</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Other wines</common:Name>
         </structure:Code>
         <structure:Code id="10">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">10</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Total wine</common:Name>
         </structure:Code>
         <structure:Code id="11">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">11</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Spirits</common:Name>
         </structure:Code>
         <structure:Code id="12">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">12</common:AnnotationText>
               </common:Annotation>
               <common:Annotation>
                  <common:AnnotationType>FURTHER_INFORMATION</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">Ready to Drink (Pre-mixed) Beverages</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">RTDs</common:Name>
         </structure:Code>
         <structure:Code id="13">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">13</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Total spirits and RTDs</common:Name>
         </structure:Code>
         <structure:Code id="15">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">14</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Cider</common:Name>
         </structure:Code>
         <structure:Code id="14">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">15</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Total all beverages</common:Name>
         </structure:Code>
      </structure:Codelist>
      <structure:Codelist id="CL_ALC_TYP" agencyID="ABS" version="1.0.0" isFinal="true">
         <common:Name xml:lang="en">Type of Volume</common:Name>
         <structure:Code id="1">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">1</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Volume of pure alcohol</common:Name>
         </structure:Code>
         <structure:Code id="2">
            <common:Annotations>
               <common:Annotation>
                  <common:AnnotationType>ORDER</common:AnnotationType>
                  <common:AnnotationText xml:lang="en">2</common:AnnotationText>
               </common:Annotation>
            </common:Annotations>
            <common:Name xml:lang="en">Volume of beverage</common:Name>
         </structure:Code>
      </structure:Codelist>
   </structure:Codelists>
   <structure:DataStructures>
      <structure:DataStructure id="ALC" agencyID="ABS" version="1.0.0" isFinal="true">
         <common:Name xml:lang="en">Apparent Consumption of Alcohol, Australia</common:Name>
         <structure:DataStructureComponents>
            <structure:DimensionList id="DimensionDescriptor">
               <structure:Dimension id="TYP" position="1">
                  <structure:ConceptIdentity>
                     <Ref id="TYP" maintainableParentID="CS_ALC" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept"/>
                  </structure:ConceptIdentity>
                  <structure:LocalRepresentation>
                     <structure:Enumeration>
                        <Ref id="CL_ALC_TYP" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist"/>
                     </structure:Enumeration>
                  </structure:LocalRepresentation>
               </structure:Dimension>
               <structure:Dimension id="MEA" position="2">
                  <structure:ConceptIdentity>
                     <Ref id="MEASURE" maintainableParentID="CS_COMMON" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept"/>
                  </structure:ConceptIdentity>
                  <structure:LocalRepresentation>
                     <structure:Enumeration>
                        <Ref id="CL_ALC_MEASURE" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist"/>
                     </structure:Enumeration>
                  </structure:LocalRepresentation>
               </structure:Dimension>
               <structure:Dimension id="BEVT" position="3">
                  <structure:ConceptIdentity>
                     <Ref id="BEVT" maintainableParentID="CS_ALC" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept"/>
                  </structure:ConceptIdentity>
                  <structure:LocalRepresentation>
                     <structure:Enumeration>
                        <Ref id="CL_ALC_BEVT" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist"/>
                     </structure:Enumeration>
                  </structure:LocalRepresentation>
               </structure:Dimension>
               <structure:Dimension id="SUB" position="4">
                  <structure:ConceptIdentity>
                     <Ref id="SUB" maintainableParentID="CS_ALC" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept"/>
                  </structure:ConceptIdentity>
                  <structure:LocalRepresentation>
                     <structure:Enumeration>
                        <Ref id="CL_ALC_SUB" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist"/>
                     </structure:Enumeration>
                  </structure:LocalRepresentation>
               </structure:Dimension>
               <structure:Dimension id="FREQUENCY" position="5">
                  <structure:ConceptIdentity>
                     <Ref id="FREQ" maintainableParentID="CS_COMMON" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept"/>
                  </structure:ConceptIdentity>
                  <structure:LocalRepresentation>
                     <structure:Enumeration>
                        <Ref id="CL_FREQ" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist"/>
                     </structure:Enumeration>
                  </structure:LocalRepresentation>
               </structure:Dimension>
               <structure:TimeDimension id="TIME_PERIOD" position="6">
                  <structure:ConceptIdentity>
                     <Ref id="TIME_PERIOD" maintainableParentID="CS_COMMON" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept"/>
                  </structure:ConceptIdentity>
                  <structure:LocalRepresentation>
                     <structure:TextFormat textType="ObservationalTimePeriod"/>
                  </structure:LocalRepresentation>
               </structure:TimeDimension>
            </structure:DimensionList>
            <structure:AttributeList id="AttributeDescriptor">
               <structure:Attribute id="UNIT_MEASURE" assignmentStatus="Conditional">
                  <structure:ConceptIdentity>
                     <Ref id="UNIT_MEASURE" maintainableParentID="CS_ATTRIBUTE" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept"/>
                  </structure:ConceptIdentity>
                  <structure:LocalRepresentation>
                     <structure:Enumeration>
                        <Ref id="CL_UNIT_MEASURE" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist"/>
                     </structure:Enumeration>
                  </structure:LocalRepresentation>
                  <structure:AttributeRelationship>
                     <structure:None/>
                  </structure:AttributeRelationship>
               </structure:Attribute>
               <structure:Attribute id="UNIT_MULT" assignmentStatus="Conditional">
                  <structure:ConceptIdentity>
                     <Ref id="UNIT_MULT" maintainableParentID="CS_ATTRIBUTE" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept"/>
                  </structure:ConceptIdentity>
                  <structure:LocalRepresentation>
                     <structure:Enumeration>
                        <Ref id="CL_UNIT_MULT" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist"/>
                     </structure:Enumeration>
                  </structure:LocalRepresentation>
                  <structure:AttributeRelationship>
                     <structure:Dimension>
                        <Ref id="MEA"/>
                     </structure:Dimension>
                  </structure:AttributeRelationship>
               </structure:Attribute>
               <structure:Attribute id="OBS_STATUS" assignmentStatus="Conditional">
                  <structure:ConceptIdentity>
                     <Ref id="OBS_STATUS" maintainableParentID="CS_ATTRIBUTE" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept"/>
                  </structure:ConceptIdentity>
                  <structure:LocalRepresentation>
                     <structure:Enumeration>
                        <Ref id="CL_OBS_STATUS" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist"/>
                     </structure:Enumeration>
                  </structure:LocalRepresentation>
                  <structure:AttributeRelationship>
                     <structure:PrimaryMeasure>
                        <Ref id="OBS_VALUE"/>
                     </structure:PrimaryMeasure>
                  </structure:AttributeRelationship>
               </structure:Attribute>
               <structure:Attribute id="OBS_COMMENT" assignmentStatus="Conditional">
                  <structure:ConceptIdentity>
                     <Ref id="OBS_COMMENT" maintainableParentID="CS_ATTRIBUTE" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept"/>
                  </structure:ConceptIdentity>
                  <structure:AttributeRelationship>
                     <structure:PrimaryMeasure>
                        <Ref id="OBS_VALUE"/>
                     </structure:PrimaryMeasure>
                  </structure:AttributeRelationship>
               </structure:Attribute>
            </structure:AttributeList>
            <structure:MeasureList id="MeasureDescriptor">
               <structure:PrimaryMeasure id="OBS_VALUE">
                  <structure:ConceptIdentity>
                     <Ref id="OBS_VALUE" maintainableParentID="CS_COMMON" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept"/>
                  </structure:ConceptIdentity>
               </structure:PrimaryMeasure>
            </structure:MeasureList>
         </structure:DataStructureComponents>
      </structure:DataStructure>
   </structure:DataStructures>
</message:Structures>
```

#### Concept

We've worked out how to get the codelists that define the values each dimension can take. However, it may not always be clear from these values what the dimensions actually are. To find this we need to look at the concept it refers to. The concept gives the dimension its meaning and its name. As codes are stored in codelists, concepts are stored in conceptschemes (conceptlists would be too obvious). So, we want the DSD to get the dimensions and their order, the referenced concepts (via their conceptschemes) to work out what they are, and the referenced codelists (to work out what values we need).

We're going back to the references query parameter again. We could use conceptscheme, but instead we’ll use the value children to tell the API we want all directly-referenced structures (which will include both the codelists, and the conceptschemes). Finally, we have all the information we need. Our API call is [https://data.api.abs.gov.au/rest/datastructure/ABS/ALC?references=children](https://data.api.abs.gov.au/rest/datastructure/ABS/ALC?references=children) (Some codelists and conceptschemes we're not using removed for brevity):

```
  <?xml version="1.0" encoding="utf-8"?>
  <!--NSI Web Service v7.13.0.0-->
  <message:Structure xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message" xmlns:structure="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure" xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
  <message:Header>
    <message:ID>IDREF1399</message:ID>
    <message:Test>false</message:Test>
    <message:Prepared>2020-09-28T11:44:17.6726618+10:00</message:Prepared>
    <message:Sender id="Unknown" />
    <message:Receiver id="Unknown" />
  </message:Header>
  <message:Structures>
    <structure:Codelists>
      <structure:Codelist id="CL_ALC_BEVT" agencyID="ABS" version="1.0.0" isFinal="true">
        <common:Name xml:lang="en">Beverage Type</common:Name>
        <structure:Code id="1">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">1</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Beer</common:Name>
        </structure:Code>
        <structure:Code id="2">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">2</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Wine</common:Name>
        </structure:Code>
        <structure:Code id="3">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">3</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Spirits and RTDs</common:Name>
        </structure:Code>
        <structure:Code id="4">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">4</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Total all beverages</common:Name>
        </structure:Code>
        <structure:Code id="5">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">5</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Cider</common:Name>
        </structure:Code>
      </structure:Codelist>
      <structure:Codelist id="CL_ALC_MEASURE" agencyID="ABS" version="1.0.0" isFinal="true">
        <common:Name xml:lang="en">Measure</common:Name>
        <structure:Code id="1">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">1</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Total apparent consumption ('000 litres)</common:Name>
        </structure:Code>
        <structure:Code id="2">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">2</common:AnnotationText>
            </common:Annotation>
            <common:Annotation>
              <common:AnnotationType>FURTHER_INFORMATION</common:AnnotationType>
              <common:AnnotationText xml:lang="en">Litres per person aged 15 years and over</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Per capita apparent consumption (litres)</common:Name>
        </structure:Code>
      </structure:Codelist>
      <structure:Codelist id="CL_ALC_SUB" agencyID="ABS" version="1.0.0" isFinal="true">
        <common:Name xml:lang="en">Beverage Subtype/Strength</common:Name>
        <structure:Code id="1">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">1</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Low alcohol beer</common:Name>
        </structure:Code>
        <structure:Code id="2">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">2</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Other alcohol beer</common:Name>
        </structure:Code>
        <structure:Code id="3">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">3</common:AnnotationText>
            </common:Annotation>
            <common:Annotation>
              <common:AnnotationType>FURTHER_INFORMATION</common:AnnotationType>
              <common:AnnotationText xml:lang="en">Alcohol volume of low strength beer is greater than 1.15% and less than or equal to 3.0%</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Low strength beer</common:Name>
        </structure:Code>
        <structure:Code id="4">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">4</common:AnnotationText>
            </common:Annotation>
            <common:Annotation>
              <common:AnnotationType>FURTHER_INFORMATION</common:AnnotationType>
              <common:AnnotationText xml:lang="en">Alcohol volume of mid strength beer is greater than 3.0% and less than or equal to 3.5%</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Mid strength beer</common:Name>
        </structure:Code>
        <structure:Code id="5">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">5</common:AnnotationText>
            </common:Annotation>
            <common:Annotation>
              <common:AnnotationType>FURTHER_INFORMATION</common:AnnotationType>
              <common:AnnotationText xml:lang="en">Alcohol volume of full strength beer is greater than 3.5%</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Full strength beer</common:Name>
        </structure:Code>
        <structure:Code id="6">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">6</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Total beer</common:Name>
        </structure:Code>
        <structure:Code id="7">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">7</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">White table wine</common:Name>
        </structure:Code>
        <structure:Code id="8">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">8</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Red table wine</common:Name>
        </structure:Code>
        <structure:Code id="9">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">9</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Other wines</common:Name>
        </structure:Code>
        <structure:Code id="10">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">10</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Total wine</common:Name>
        </structure:Code>
        <structure:Code id="11">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">11</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Spirits</common:Name>
        </structure:Code>
        <structure:Code id="12">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">12</common:AnnotationText>
            </common:Annotation>
            <common:Annotation>
              <common:AnnotationType>FURTHER_INFORMATION</common:AnnotationType>
              <common:AnnotationText xml:lang="en">Ready to Drink (Pre-mixed) Beverages</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">RTDs</common:Name>
        </structure:Code>
        <structure:Code id="13">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">13</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Total spirits and RTDs</common:Name>
        </structure:Code>
        <structure:Code id="15">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">14</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Cider</common:Name>
        </structure:Code>
        <structure:Code id="14">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">15</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Total all beverages</common:Name>
        </structure:Code>
      </structure:Codelist>
      <structure:Codelist id="CL_ALC_TYP" agencyID="ABS" version="1.0.0" isFinal="true">
        <common:Name xml:lang="en">Type of Volume</common:Name>
        <structure:Code id="1">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">1</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Volume of pure alcohol</common:Name>
        </structure:Code>
        <structure:Code id="2">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>ORDER</common:AnnotationType>
              <common:AnnotationText xml:lang="en">2</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Volume of beverage</common:Name>
        </structure:Code>
      </structure:Codelist>
      <structure:Codelist id="CL_FREQ" agencyID="ABS" version="1.0.0" isFinal="true">
        <common:Name xml:lang="en">Frequency</common:Name>
        <structure:Code id="H">
          <common:Name xml:lang="en">Hourly</common:Name>
          <common:Description xml:lang="en">To be used for data collected or disseminated every hour.</common:Description>
        </structure:Code>
        <structure:Code id="D">
          <common:Name xml:lang="en">Daily</common:Name>
          <common:Description xml:lang="en">To be used for data collected or disseminated every day.</common:Description>
        </structure:Code>
        <structure:Code id="N">
          <common:Name xml:lang="en">Minutely</common:Name>
          <common:Description xml:lang="en">While N denotes "minutely", usually, there may be no observations every minute (for several series the frequency is usually "irregular" within a day/days). And though observations may be sparse (not collected or disseminated every minute), missing values do not need to be given for the minutes when no observations exist: in any case the time stamp determines when an observation is observed.</common:Description>
        </structure:Code>
        <structure:Code id="B">
          <common:Name xml:lang="en">Daily or businessweek</common:Name>
          <common:Description xml:lang="en">Similar to "daily", however there are no observations for Saturdays and Sundays (so, neither "missing values" nor "numeric values" should be provided for Saturday and Sunday). This treatment ("business") is one way to deal with such cases, but it is not the only option. Such a time series could alternatively be considered daily ("D"), thus, with missing values in the weekend.</common:Description>
        </structure:Code>
        <structure:Code id="W">
          <common:Name xml:lang="en">Weekly</common:Name>
          <common:Description xml:lang="en">To be used for data collected or disseminated every week.</common:Description>
        </structure:Code>
        <structure:Code id="S">
          <common:Name xml:lang="en">Half-yearly, semester</common:Name>
          <common:Description xml:lang="en">To be used for data collected or disseminated every semester.</common:Description>
        </structure:Code>
        <structure:Code id="A">
          <common:Name xml:lang="en">Annual</common:Name>
          <common:Description xml:lang="en">To be used for data collected or disseminated every year.</common:Description>
        </structure:Code>
        <structure:Code id="M">
          <common:Name xml:lang="en">Monthly</common:Name>
          <common:Description xml:lang="en">To be used for data collected or disseminated every month.</common:Description>
        </structure:Code>
        <structure:Code id="Q">
          <common:Name xml:lang="en">Quarterly</common:Name>
          <common:Description xml:lang="en">To be used for data collected or disseminated every quarter.</common:Description>
        </structure:Code>
      </structure:Codelist>
      <structure:Codelist id="CL_OBS_STATUS" agencyID="ABS" version="1.0.0" isFinal="true">
        <!-- Removed codelist -->
      </structure:Codelist>
      <structure:Codelist id="CL_UNIT_MEASURE" agencyID="ABS" version="1.0.0" isFinal="true">
        <!-- Removed codelist -->
      </structure:Codelist>
      <structure:Codelist id="CL_UNIT_MULT" agencyID="ABS" version="1.0.0" isFinal="true">
        <!-- Removed codelist -->
      </structure:Codelist>
    </structure:Codelists>
    <structure:Concepts>
      <structure:ConceptScheme id="CS_ALC" agencyID="ABS" version="1.0.0" isFinal="true">
        <common:Name xml:lang="en">Apparent Consumption of Alcohol Concepts</common:Name>
        <structure:Concept id="BEVT">
          <common:Name xml:lang="en">Beverage Type</common:Name>
        </structure:Concept>
        <structure:Concept id="SUB">
          <common:Name xml:lang="en">Beverage Subtype/Strength</common:Name>
        </structure:Concept>
        <structure:Concept id="TYP">
          <common:Name xml:lang="en">Type of Volume</common:Name>
        </structure:Concept>
      </structure:ConceptScheme>
      <structure:ConceptScheme id="CS_ATTRIBUTE" agencyID="ABS" version="1.0.0" isFinal="true">
        <!-- Remove conceptscheme -->
      </structure:ConceptScheme>
      <structure:ConceptScheme id="CS_COMMON" agencyID="ABS" version="1.0.0" isFinal="true">
        <common:Name xml:lang="en">Common Concepts</common:Name>
        <structure:Concept id="OBS_VALUE">
          <common:Name xml:lang="en">Observation Value</common:Name>
          <common:Description xml:lang="en">The observed value of the variable identified by the series dimension values.</common:Description>
        </structure:Concept>
        <structure:Concept id="TIME_PERIOD">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>CONTEXT</common:AnnotationType>
              <common:AnnotationText xml:lang="en">The measurement represented by each observation corresponds to a specific point in time (e.g. a single day) or a period (e.g. a month, a fiscal year, or a calendar year).</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Time Period</common:Name>
          <common:Description xml:lang="en">Timespan or point in time for which the observation refers.</common:Description>
        </structure:Concept>
        <structure:Concept id="FREQ">
          <common:Name xml:lang="en">Frequency</common:Name>
          <common:Description xml:lang="en">Rate at which data is collated.</common:Description>
        </structure:Concept>
        <structure:Concept id="MEASURE">
          <common:Name xml:lang="en">Measure</common:Name>
        </structure:Concept>
        <structure:Concept id="TSEST">
          <common:Annotations>
            <common:Annotation>
              <common:AnnotationType>OTHER_LINKS</common:AnnotationType>
              <common:AnnotationText xml:lang="en">https://www.abs.gov.au/websitedbs/D3310114.nsf/home/Time+Series+Analysis:+The+Basics</common:AnnotationText>
            </common:Annotation>
          </common:Annotations>
          <common:Name xml:lang="en">Adjustment Type</common:Name>
          <common:Description xml:lang="en">An original time series can be decomposed into three components: the trend (the general direction of the series), the seasonal component (systematic, calendar related movements) and the irregular component (unsystematic, short term fluctuations). Seasonally adjusted series are produced by estimating the seasonal component and removing this from the original series. In most economic data the seasonal component is a combination of seasonal influences (e.g. the effect of the weather or social traditions) plus other kinds of calendar related variations such as Chinese New Year and Christmas. The seasonal adjustment methodology takes into account both seasonal and other calendar related factors that evolve over time to reflect changes in activity patterns.</common:Description>
        </structure:Concept>
      </structure:ConceptScheme>
    </structure:Concepts>
    <structure:DataStructures>
      <structure:DataStructure id="ALC" agencyID="ABS" version="1.0.0" isFinal="true">
        <common:Name xml:lang="en">Apparent Consumption of Alcohol, Australia</common:Name>
        <structure:DataStructureComponents>
          <structure:DimensionList id="DimensionDescriptor">
            <structure:Dimension id="TYP" position="1">
              <structure:ConceptIdentity>
                <Ref id="TYP" maintainableParentID="CS_ALC" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept" />
              </structure:ConceptIdentity>
              <structure:LocalRepresentation>
                <structure:Enumeration>
                  <Ref id="CL_ALC_TYP" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist" />
                </structure:Enumeration>
              </structure:LocalRepresentation>
            </structure:Dimension>
            <structure:Dimension id="MEA" position="2">
              <structure:ConceptIdentity>
                <Ref id="MEASURE" maintainableParentID="CS_COMMON" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept" />
              </structure:ConceptIdentity>
              <structure:LocalRepresentation>
                <structure:Enumeration>
                  <Ref id="CL_ALC_MEASURE" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist" />
                </structure:Enumeration>
              </structure:LocalRepresentation>
            </structure:Dimension>
            <structure:Dimension id="BEVT" position="3">
              <structure:ConceptIdentity>
                <Ref id="BEVT" maintainableParentID="CS_ALC" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept" />
              </structure:ConceptIdentity>
              <structure:LocalRepresentation>
                <structure:Enumeration>
                  <Ref id="CL_ALC_BEVT" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist" />
                </structure:Enumeration>
              </structure:LocalRepresentation>
            </structure:Dimension>
            <structure:Dimension id="SUB" position="4">
              <structure:ConceptIdentity>
                <Ref id="SUB" maintainableParentID="CS_ALC" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept" />
              </structure:ConceptIdentity>
              <structure:LocalRepresentation>
                <structure:Enumeration>
                  <Ref id="CL_ALC_SUB" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist" />
                </structure:Enumeration>
              </structure:LocalRepresentation>
            </structure:Dimension>
            <structure:Dimension id="FREQUENCY" position="5">
              <structure:ConceptIdentity>
                <Ref id="FREQ" maintainableParentID="CS_COMMON" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept" />
              </structure:ConceptIdentity>
              <structure:LocalRepresentation>
                <structure:Enumeration>
                  <Ref id="CL_FREQ" version="1.0.0" agencyID="ABS" package="codelist" class="Codelist" />
                </structure:Enumeration>
              </structure:LocalRepresentation>
            </structure:Dimension>
            <structure:TimeDimension id="TIME_PERIOD" position="6">
              <structure:ConceptIdentity>
                <Ref id="TIME_PERIOD" maintainableParentID="CS_COMMON" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept" />
              </structure:ConceptIdentity>
              <structure:LocalRepresentation>
                <structure:TextFormat textType="ObservationalTimePeriod" />
              </structure:LocalRepresentation>
            </structure:TimeDimension>
          </structure:DimensionList>
          <structure:AttributeList id="AttributeDescriptor">
            <!-- Removed attributes -->
          </structure:AttributeList>
          <structure:MeasureList id="MeasureDescriptor">
            <structure:PrimaryMeasure id="OBS_VALUE">
              <structure:ConceptIdentity>
                <Ref id="OBS_VALUE" maintainableParentID="CS_COMMON" maintainableParentVersion="1.0.0" agencyID="ABS" package="conceptscheme" class="Concept" />
              </structure:ConceptIdentity>
            </structure:PrimaryMeasure>
          </structure:MeasureList>
        </structure:DataStructureComponents>
      </structure:DataStructure>
    </structure:DataStructures>
  </message:Structures>
</message:Structure>
```

From the retrieved XML we can construct an idea of the dimensions:

-   Type of Volume

-   Measure
-   Beverage Type

-   Beverage Subtype/Strength
-   Reporting frequency

-   Time period

We'll leave time period off for now, as it's handled differently to other dimensions. But by looking at the codelists I can identify that I want the following values:

-   Type of Volume: Volume of beverage, code value 1

-   Measure: Per capita apparent consumption (litres), code value 2
-   Beverage Type: Beer, code value 1

-   Beverage Subtype/Strength: Mid strength beer, code value 4
-   Reporting frequency: Annual, code value A

---
Source: [Worked Examples](https://www.abs.gov.au/statistics/application-programming-interfaces-apis/data-api-user-guide/worked-examples)